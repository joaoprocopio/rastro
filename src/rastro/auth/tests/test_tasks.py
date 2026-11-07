import asyncio
import logging
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any

import httpx
import pytest
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.tasks import Task
from procrastinate.testing import InMemoryConnector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.errors import (
    EmailNoAnswerError,
    EmailRefusedError,
    EmailTemporaryError,
)
from rastro.auth.domain.value_objects import (
    ResetToken,
    ResetTokenCooldown,
)
from rastro.auth.infrastructure.models import ResetTokenRow
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
)
from rastro.auth.presentation import tasks
from rastro.auth.presentation.tasks import (
    password_reset_remove_old_jobs_task,
    password_reset_send_task,
    reset_token_remove_expired_task,
    session_remove_expired_task,
)
from rastro.auth.tests.conftest import JobHistory, until_a_statement_waits
from rastro.auth.tests.fakes import FakeEmailSender
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.common.presentation.dependencies import (
    JOB_SETTINGS_KEY,
)
from rastro.settings import Settings

CONFIRM_PATH = "/api/v1/auth/password-reset/confirm"
NEW_PASSWORD = "newpassword"
SEVEN_DAYS = timedelta(days=7)
MINUTE = timedelta(minutes=1)


async def test_the_task_removes_the_expired_session_and_logs_the_count(
    worker_app: App,
    reader: AsyncSession,
    active_session: Session,
    expired_session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The task reads the wall clock, as the two Session fixtures do.
    deferrer = session_remove_expired_task.configure(task_kwargs={"timestamp": 0})
    await deferrer.defer_async()

    with caplog.at_level(logging.INFO, logger=tasks.__name__):
        await worker_app.run_worker_async()

    read_sessions = SqlSessionRepository(reader)
    assert await read_sessions.get_by_hashed_token(active_session.hashed_token) == (
        active_session
    )
    assert await read_sessions.get_by_hashed_token(expired_session.hashed_token) is None
    (record,) = [record for record in caplog.records if record.name == tasks.__name__]
    assert record.getMessage() == "Expired Sessions removed: 1"


async def test_the_hourly_task_removes_the_expired_reset_token_and_logs_the_count(
    worker_app: App,
    reader: AsyncSession,
    user: User,
    expired_reset_token: ResetToken,
    other_user_reset_token: IssuedResetToken,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The task reads the wall clock, as the two Reset token fixtures do.
    deferrer = reset_token_remove_expired_task.configure(task_kwargs={"timestamp": 0})
    await deferrer.defer_async()

    with caplog.at_level(logging.INFO, logger=tasks.__name__):
        await worker_app.run_worker_async()

    read_reset_tokens = SqlResetTokenRepository(reader)
    assert await read_reset_tokens.get_by_user_id(user.id) is None
    assert await read_reset_tokens.get_by_user_id(other_user_reset_token.user_id) == (
        other_user_reset_token
    )
    (record,) = [record for record in caplog.records if record.name == tasks.__name__]
    assert record.getMessage() == "Expired Reset tokens removed: 1"


async def test_the_send_task_emails_the_user_and_commits_the_digest_of_the_token(
    worker_app: App, reader: AsyncSession, email_sender: FakeEmailSender, user: User
) -> None:
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.SUCCEEDED
    (email,) = email_sender.sent
    assert email.to == user.email
    stored = await SqlResetTokenRepository(reader).get_by_user_id(user.id)
    assert stored is not None
    assert stored.hashed_token == email_sender.last_reset_token().digest()


async def test_the_send_task_sends_nothing_for_an_address_with_no_user(
    worker_app: App, reader: AsyncSession, email_sender: FakeEmailSender
) -> None:
    job_id = await password_reset_send_task.defer_async(email="nobody@example.com")

    await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.SUCCEEDED
    assert email_sender.sent == []
    assert await reader.scalar(select(ResetTokenRow)) is None


async def test_the_reset_token_table_and_the_job_arguments_hold_no_token_of_the_link(
    worker_app: App, reader: AsyncSession, email_sender: FakeEmailSender, user: User
) -> None:
    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    await worker_app.run_worker_async()

    token = email_sender.last_reset_token().root.get_secret_value()
    assert connector.jobs[job_id]["args"] == {"email": user.email.root}
    (row,) = (await reader.execute(text("SELECT * FROM auth_reset_token"))).all()
    assert token not in str(row)
    assert token.encode() not in row.hashed_token


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(EmailRefusedError(), id="refused"),
        pytest.param(RuntimeError("a bug"), id="unexpected"),
    ],
)
async def test_a_send_that_will_not_succeed_commits_no_token_and_the_job_fails_at_once(
    worker_app: App,
    reader: AsyncSession,
    email_sender: FakeEmailSender,
    user: User,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
) -> None:
    email_sender.error = error
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    with caplog.at_level(logging.ERROR):
        await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.FAILED
    assert await reader.scalar(select(ResetTokenRow)) is None
    (record,) = [record for record in caplog.records if record.exc_info]
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None
    assert record.exc_info[1] is error


async def test_a_temporary_failure_commits_no_token_and_the_job_waits_for_its_retry(
    worker_app: App,
    connector: InMemoryConnector,
    reader: AsyncSession,
    email_sender: FakeEmailSender,
    user: User,
) -> None:
    email_sender.error = EmailTemporaryError()
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.TODO
    assert connector.jobs[job_id]["attempts"] == 1
    assert await reader.scalar(select(ResetTokenRow)) is None
    assert email_sender.sent == []


async def test_a_temporary_failure_on_every_attempt_backs_off_and_ends_as_failed(
    worker_app: App,
    connector: InMemoryConnector,
    reader: AsyncSession,
    email_sender: FakeEmailSender,
    user: User,
    caplog: pytest.LogCaptureFixture,
) -> None:
    email_sender.error = EmailTemporaryError()
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    for seconds in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]:
        wait = timedelta(seconds=seconds)
        started = datetime.now(UTC)
        await worker_app.run_worker_async()
        finished = datetime.now(UTC)
        retry_at = connector.jobs[job_id]["scheduled_at"]
        assert started + wait <= retry_at <= finished + wait
        connector.jobs[job_id]["scheduled_at"] = None
    with caplog.at_level(logging.ERROR):
        await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.FAILED
    assert connector.jobs[job_id]["attempts"] == 11
    assert await reader.scalar(select(ResetTokenRow)) is None


async def test_a_send_with_no_answer_commits_the_token_and_succeeds_with_a_warning(
    worker_app: App,
    reader: AsyncSession,
    email_sender: FakeEmailSender,
    user: User,
    caplog: pytest.LogCaptureFixture,
) -> None:
    email_sender.error = EmailNoAnswerError()
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    with caplog.at_level(logging.WARNING, logger=tasks.__name__):
        await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.SUCCEEDED
    assert await SqlResetTokenRepository(reader).get_by_user_id(user.id) is not None
    (record,) = [record for record in caplog.records if record.name == tasks.__name__]
    assert record.levelno == logging.WARNING
    assert record.getMessage() == (
        f"The SMTP server gave no answer to the reset email of job {job_id}, "
        "which may have gone out."
    )


async def test_an_address_that_breaks_its_value_object_fails_the_job(
    worker_app: App, email_sender: FakeEmailSender, caplog: pytest.LogCaptureFixture
) -> None:
    job_id = await password_reset_send_task.defer_async(email="not-an-email")

    with caplog.at_level(logging.ERROR):
        await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.FAILED
    assert email_sender.sent == []


async def test_a_second_job_applies_the_cooldown_of_the_settings_of_the_worker(
    worker_app: App,
    settings: Settings,
    email_sender: FakeEmailSender,
    user: User,
    reset_token: ResetToken,
) -> None:
    # The default of 60s would hold the email, because the fixture issued the token now.
    shorter = settings.model_copy(
        update={"reset_token_cooldown": ResetTokenCooldown(timedelta(microseconds=1))}
    )
    await password_reset_send_task.defer_async(email=user.email.root)

    await worker_app.run_worker_async(
        additional_context={
            **worker_app.worker_defaults["additional_context"],
            JOB_SETTINGS_KEY: shorter,
        }
    )

    (email,) = email_sender.sent
    assert email.to == user.email


async def test_a_second_job_within_the_default_cooldown_sends_nothing(
    worker_app: App,
    email_sender: FakeEmailSender,
    user: User,
    reset_token: ResetToken,
) -> None:
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.SUCCEEDED
    assert email_sender.sent == []


async def _run_two_jobs_where_one_waits_for_the_other(
    worker_app: App,
    *,
    user: User,
    context: dict[str, object],
    engine: AsyncEngine,
    held_email_sender: FakeEmailSender,
) -> list[int]:
    assert held_email_sender.hold is not None
    job_ids = [
        await password_reset_send_task.defer_async(email=user.email.root)
        for _ in range(2)
    ]
    worker = asyncio.create_task(
        worker_app.run_worker_async(concurrency=2, additional_context=context)
    )
    async with create_sessionmaker(engine)() as probe:
        try:
            await until_a_statement_waits(
                probe, statement="INSERT INTO auth_reset_token%"
            )
        finally:
            held_email_sender.hold.set()
    await worker
    return job_ids


async def _stored_digest(engine: AsyncEngine, *, user: User) -> bytes:
    async with create_sessionmaker(engine)() as reader:
        (row,) = await reader.scalars(
            select(ResetTokenRow).where(ResetTokenRow.user_id == user.id.root)
        )
    return row.hashed_token


async def test_two_jobs_at_the_same_time_send_one_email_whose_token_works(
    worker_app: App,
    engine: AsyncEngine,
    committing_job_context: dict[str, object],
    held_email_sender: FakeEmailSender,
    committing_client: httpx.AsyncClient,
    committed_user: User,
) -> None:
    job_ids = await _run_two_jobs_where_one_waits_for_the_other(
        worker_app,
        user=committed_user,
        context=committing_job_context,
        engine=engine,
        held_email_sender=held_email_sender,
    )

    for job_id in job_ids:
        status = await worker_app.job_manager.get_job_status_async(job_id)
        assert status == Status.SUCCEEDED
    (email,) = held_email_sender.sent
    assert email.to == committed_user.email
    token = held_email_sender.last_reset_token()
    assert await _stored_digest(engine, user=committed_user) == token.digest().root
    confirmed = await committing_client.post(
        CONFIRM_PATH,
        json={"token": token.root.get_secret_value(), "password": NEW_PASSWORD},
    )
    assert confirmed.status_code == HTTPStatus.NO_CONTENT


async def test_a_job_that_rolls_back_leaves_the_write_and_the_email_to_the_waiting_job(
    worker_app: App,
    engine: AsyncEngine,
    committing_job_context: dict[str, object],
    held_email_sender: FakeEmailSender,
    committed_user: User,
) -> None:
    held_email_sender.next_error = EmailTemporaryError()

    job_ids = await _run_two_jobs_where_one_waits_for_the_other(
        worker_app,
        user=committed_user,
        context=committing_job_context,
        engine=engine,
        held_email_sender=held_email_sender,
    )

    statuses = {
        await worker_app.job_manager.get_job_status_async(job_id) for job_id in job_ids
    }
    assert statuses == {Status.TODO, Status.SUCCEEDED}
    assert len(held_email_sender.sent) == 1
    assert await _stored_digest(engine, user=committed_user) == (
        held_email_sender.last_reset_token().digest().root
    )


async def test_the_retry_of_a_job_that_rolled_back_keeps_the_token_of_the_last_email(
    worker_app: App,
    connector: InMemoryConnector,
    engine: AsyncEngine,
    committing_job_context: dict[str, object],
    held_email_sender: FakeEmailSender,
    committing_client: httpx.AsyncClient,
    committed_user: User,
) -> None:
    held_email_sender.next_error = EmailTemporaryError()
    await _run_two_jobs_where_one_waits_for_the_other(
        worker_app,
        user=committed_user,
        context=committing_job_context,
        engine=engine,
        held_email_sender=held_email_sender,
    )
    (retried,) = [
        job_id
        for job_id, job in connector.jobs.items()
        if job["status"] == Status.TODO.value
    ]
    connector.jobs[retried]["scheduled_at"] = None

    await worker_app.run_worker_async(additional_context=committing_job_context)

    status = await worker_app.job_manager.get_job_status_async(retried)
    assert status == Status.SUCCEEDED
    assert len(held_email_sender.sent) == 1
    token = held_email_sender.last_reset_token()
    assert await _stored_digest(engine, user=committed_user) == token.digest().root
    confirmed = await committing_client.post(
        CONFIRM_PATH,
        json={"token": token.root.get_secret_value(), "password": NEW_PASSWORD},
    )
    assert confirmed.status_code == HTTPStatus.NO_CONTENT


async def test_the_send_job_runs_on_its_own_queue(worker_app: App) -> None:
    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)

    job_id = await password_reset_send_task.defer_async(email="ana@example.com")

    assert connector.jobs[job_id]["queue_name"] == tasks.PASSWORD_RESET_QUEUE


async def test_the_daily_task_removes_an_old_succeeded_job_and_an_old_failed_one(
    connector_app: App, job_history: JobHistory
) -> None:
    await job_history.finish(status=Status.SUCCEEDED, age=SEVEN_DAYS + MINUTE)
    await job_history.finish(status=Status.FAILED, age=SEVEN_DAYS + MINUTE)
    deferrer = password_reset_remove_old_jobs_task.configure(
        task_kwargs={"timestamp": 0}
    )
    daily_job_id = await deferrer.defer_async()

    await connector_app.run_worker_async()

    assert await job_history.statuses() == {daily_job_id: Status.SUCCEEDED.value}


@pytest.mark.parametrize("status", [Status.SUCCEEDED, Status.FAILED])
async def test_the_daily_task_keeps_a_reset_job_younger_than_7_days(
    connector_app: App, job_history: JobHistory, status: Status
) -> None:
    job_id = await job_history.finish(status=status, age=SEVEN_DAYS - MINUTE)
    deferrer = password_reset_remove_old_jobs_task.configure(
        task_kwargs={"timestamp": 0}
    )
    daily_job_id = await deferrer.defer_async()

    await connector_app.run_worker_async()

    assert await job_history.statuses() == {
        job_id: status.value,
        daily_job_id: Status.SUCCEEDED.value,
    }


@pytest.mark.parametrize("status", [Status.SUCCEEDED, Status.FAILED])
async def test_the_daily_task_keeps_an_old_job_of_another_queue(
    connector_app: App, job_history: JobHistory, status: Status
) -> None:
    job_id = await job_history.finish(
        status=status, age=SEVEN_DAYS + MINUTE, queue="other"
    )
    deferrer = password_reset_remove_old_jobs_task.configure(
        task_kwargs={"timestamp": 0}
    )
    daily_job_id = await deferrer.defer_async()

    await connector_app.run_worker_async()

    assert await job_history.statuses() == {
        job_id: status.value,
        daily_job_id: Status.SUCCEEDED.value,
    }


@pytest.mark.parametrize(
    ("task", "cron"),
    [
        (reset_token_remove_expired_task, "0 * * * *"),
        (password_reset_remove_old_jobs_task, "0 0 * * *"),
    ],
)
async def test_a_cleanup_task_runs_on_its_schedule(
    worker_app: App, task: Task[Any, Any, Any], cron: str
) -> None:
    periodic_task = worker_app.periodic_registry.periodic_tasks[task.name, ""]

    assert periodic_task.cron == cron
