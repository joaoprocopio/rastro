import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.testing import InMemoryConnector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    ResetToken,
    ResetTokenCooldown,
)
from rastro.auth.infrastructure.models import ResetTokenRow
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.presentation import tasks
from rastro.auth.presentation.dependencies import JOB_EMAIL_SENDER_KEY
from rastro.auth.presentation.tasks import (
    password_reset_send_task,
    session_remove_expired_task,
)
from rastro.auth.tests.conftest import until_a_statement_waits
from rastro.auth.tests.fakes import FakeEmailSender
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.common.presentation.dependencies import (
    JOB_SESSIONMAKER_KEY,
    JOB_SETTINGS_KEY,
)
from rastro.settings import Settings


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


@pytest.fixture
async def committed_user(engine: AsyncEngine) -> AsyncIterator[User]:
    """A User that every connection sees, which the test does not roll back."""
    sessionmaker = create_sessionmaker(engine)
    async with sessionmaker.begin() as db_session:
        users = SqlUserRepository(db_session)
        user = User(
            id=await users.next_id(),
            email=Email("committed@example.com"),
            display_name=DisplayName("Committed"),
            hashed_password=HashedPassword("fake$password"),
        )
        await users.add(user)

    yield user

    # The foreign key deletes the Reset token with its User.
    async with sessionmaker.begin() as db_session:
        await db_session.execute(
            text("DELETE FROM auth_user WHERE id = :id"), {"id": user.id.root}
        )


async def test_two_jobs_at_the_same_time_leave_one_token_of_the_last_email(
    worker_app: App, engine: AsyncEngine, settings: Settings, committed_user: User
) -> None:
    sessionmaker = create_sessionmaker(engine)
    email_sender = FakeEmailSender()
    email_sender.hold = asyncio.Event()
    job_ids = [
        await password_reset_send_task.defer_async(email=committed_user.email.root)
        for _ in range(2)
    ]

    # Each job commits on its own connection, so the row lock of one holds the other.
    worker = asyncio.create_task(
        worker_app.run_worker_async(
            concurrency=2,
            additional_context={
                JOB_SESSIONMAKER_KEY: sessionmaker,
                JOB_SETTINGS_KEY: settings,
                JOB_EMAIL_SENDER_KEY: email_sender,
            },
        )
    )
    async with sessionmaker() as probe:
        try:
            await until_a_statement_waits(
                probe, statement="INSERT INTO auth_reset_token%"
            )
        finally:
            email_sender.hold.set()
    await worker

    for job_id in job_ids:
        status = await worker_app.job_manager.get_job_status_async(job_id)
        assert status == Status.SUCCEEDED
    assert len(email_sender.sent) == 2
    async with sessionmaker() as reader:
        (row,) = await reader.scalars(
            select(ResetTokenRow).where(ResetTokenRow.user_id == committed_user.id.root)
        )
    assert row.hashed_token == email_sender.last_reset_token().digest().root


async def test_the_send_job_runs_on_its_own_queue(worker_app: App) -> None:
    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)

    job_id = await password_reset_send_task.defer_async(email="ana@example.com")

    assert connector.jobs[job_id]["queue_name"] == tasks.PASSWORD_RESET_QUEUE
