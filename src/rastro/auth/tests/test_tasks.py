import logging
from datetime import timedelta
from typing import Any

import pytest
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.tasks import Task
from procrastinate.testing import InMemoryConnector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.value_objects import ResetToken
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
from rastro.auth.tests.conftest import JobHistory
from rastro.auth.tests.fakes import FakeEmailSender

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


async def test_a_send_that_raises_commits_no_token_and_the_job_fails(
    worker_app: App,
    reader: AsyncSession,
    email_sender: FakeEmailSender,
    user: User,
    caplog: pytest.LogCaptureFixture,
) -> None:
    email_sender.error = RuntimeError("the server is down")
    job_id = await password_reset_send_task.defer_async(email=user.email.root)

    with caplog.at_level(logging.ERROR):
        await worker_app.run_worker_async()

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.FAILED
    assert await reader.scalar(select(ResetTokenRow)) is None


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
