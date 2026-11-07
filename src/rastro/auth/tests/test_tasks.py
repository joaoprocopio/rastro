import logging
from datetime import UTC, datetime, timedelta

import pytest
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.testing import InMemoryConnector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import (
    EmailNoAnswerError,
    EmailRefusedError,
    EmailTemporaryError,
)
from rastro.auth.infrastructure.models import ResetTokenRow
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
)
from rastro.auth.presentation import tasks
from rastro.auth.presentation.tasks import (
    password_reset_send_task,
    session_remove_expired_task,
)
from rastro.auth.tests.fakes import FakeEmailSender


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


async def test_the_send_job_runs_on_its_own_queue(worker_app: App) -> None:
    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)

    job_id = await password_reset_send_task.defer_async(email="ana@example.com")

    assert connector.jobs[job_id]["queue_name"] == tasks.PASSWORD_RESET_QUEUE
