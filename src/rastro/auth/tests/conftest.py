import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from email import message_from_bytes, policy
from email.message import EmailMessage

import httpx
import pytest
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, LoginPassword
from aiosmtpd.smtp import Session as SmtpSession
from fastapi import FastAPI
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.testing import InMemoryConnector
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.ports import PasswordHasher
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    RawPassword,
    ResetToken,
    SessionToken,
)
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.presentation.tasks import (
    PASSWORD_RESET_QUEUE,
    password_reset_send_task,
)
from rastro.settings import Settings, SmtpSecurity


@pytest.fixture
async def user(db_session: AsyncSession, password_hasher: PasswordHasher) -> User:
    users = SqlUserRepository(db_session)
    user = User(
        id=await users.next_id(),
        email=Email("ana@example.com"),
        display_name=DisplayName("Ana"),
        hashed_password=password_hasher.hash(
            password=RawPassword(SecretStr("password"))
        ),
    )
    await users.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def active_session(
    db_session: AsyncSession, user: User, settings: Settings
) -> Session:
    """A committed Session of `user` that starts now, by the wall clock."""
    sessions = SqlSessionRepository(db_session)
    session = Session.start(
        id=await sessions.next_id(),
        user_id=user.id,
        token=SessionToken(SecretStr("active")),
        at=datetime.now(UTC),
        lifetime=settings.session_lifetime,
    )
    await sessions.add(session)
    await db_session.commit()
    return session


@pytest.fixture
async def expired_session(
    db_session: AsyncSession, user: User, settings: Settings
) -> Session:
    """A committed Session of `user` whose lifetime runs out now, by the wall clock."""
    sessions = SqlSessionRepository(db_session)
    session = Session.start(
        id=await sessions.next_id(),
        user_id=user.id,
        token=SessionToken(SecretStr("expired")),
        at=datetime.now(UTC) - settings.session_lifetime.root,
        lifetime=settings.session_lifetime,
    )
    await sessions.add(session)
    await db_session.commit()
    return session


@pytest.fixture
async def reset_token(
    db_session: AsyncSession, user: User, settings: Settings
) -> ResetToken:
    """The token of a committed Reset token of `user`, issued now by the wall clock."""
    token = ResetToken(SecretStr("reset"))
    reset_tokens = SqlResetTokenRepository(db_session)
    await reset_tokens.replace(
        IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=user.id,
            token=token,
            at=datetime.now(UTC),
            lifetime=settings.reset_token_lifetime,
        )
    )
    await db_session.commit()
    return token


@pytest.fixture
async def expired_reset_token(
    db_session: AsyncSession, user: User, settings: Settings
) -> ResetToken:
    """The token of a committed Reset token of `user` whose lifetime runs out now."""
    token = ResetToken(SecretStr("expired"))
    reset_tokens = SqlResetTokenRepository(db_session)
    await reset_tokens.replace(
        IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=user.id,
            token=token,
            at=datetime.now(UTC) - settings.reset_token_lifetime.root,
            lifetime=settings.reset_token_lifetime,
        )
    )
    await db_session.commit()
    return token


@pytest.fixture
async def other_user_reset_token(
    db_session: AsyncSession, password_hasher: PasswordHasher, settings: Settings
) -> IssuedResetToken:
    """A committed Reset token of a second User, issued now by the wall clock."""
    users = SqlUserRepository(db_session)
    other_user = User(
        id=await users.next_id(),
        email=Email("bia@example.com"),
        display_name=DisplayName("Bia"),
        hashed_password=password_hasher.hash(
            password=RawPassword(SecretStr("password"))
        ),
    )
    await users.add(other_user)
    reset_tokens = SqlResetTokenRepository(db_session)
    reset_token = IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=other_user.id,
        token=ResetToken(SecretStr("other")),
        at=datetime.now(UTC),
        lifetime=settings.reset_token_lifetime,
    )
    await reset_tokens.replace(reset_token)
    await db_session.commit()
    return reset_token


@pytest.fixture
async def postgres_worker_app(
    unbound_worker_app: App, engine: AsyncEngine
) -> AsyncIterator[App]:
    """`unbound_worker_app` on its real connector, whose jobs commit in the test database."""
    async with unbound_worker_app.open_async():
        yield unbound_worker_app
        # These rows sit outside the transaction of the test, so no rollback removes them.
        connector = unbound_worker_app.connector
        await connector.execute_query_async("DELETE FROM procrastinate_jobs")
        await connector.execute_query_async("DELETE FROM procrastinate_workers")


@pytest.fixture(params=["worker_app", "postgres_worker_app"])
def connector_app(request: pytest.FixtureRequest) -> App:
    """The App of a job test that runs once on `InMemoryConnector` and once on Postgres."""
    app: App = request.getfixturevalue(request.param)
    return app


class JobHistory:
    """Writes reset jobs that finished in the past, and reads the jobs of its App."""

    def __init__(self, app: App) -> None:
        self._app = app

    async def finish(
        self, *, status: Status, age: timedelta, queue: str = PASSWORD_RESET_QUEUE
    ) -> int:
        deferrer = password_reset_send_task.configure(
            queue=queue, task_kwargs={"email": "ana@example.com"}
        )
        job_id = await deferrer.defer_async()
        job_manager = self._app.job_manager
        job = await job_manager.fetch_job(
            queues=[queue], worker_id=await job_manager.register_worker()
        )
        assert job is not None
        await job_manager.finish_job(job, status=status, delete_job=False)
        await self._move_events(job_id, at=datetime.now(UTC) - age)
        return job_id

    async def statuses(self) -> dict[int | None, str | None]:
        jobs = await self._app.job_manager.list_jobs_async()
        return {job.id: job.status for job in jobs}

    # remove_old_jobs reads the age of a job from its last event.
    async def _move_events(self, job_id: int, *, at: datetime) -> None:
        connector = self._app.connector
        if isinstance(connector, InMemoryConnector):
            for event in connector.events[job_id]:
                event["at"] = at
        else:
            await connector.execute_query_async(
                "UPDATE procrastinate_events SET at = %(at)s WHERE job_id = %(job_id)s",
                at=at,
                job_id=job_id,
            )


@pytest.fixture
def job_history(connector_app: App) -> JobHistory:
    return JobHistory(connector_app)


class SmtpRecorder:
    """The handler of `smtp_server`, which records what the server receives."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []
        self.logins: list[tuple[str, str]] = []

    async def handle_DATA(
        self, server: SMTP, session: SmtpSession, envelope: Envelope
    ) -> str:
        assert isinstance(envelope.content, bytes)
        message = message_from_bytes(envelope.content, policy=policy.default)
        assert isinstance(message, EmailMessage)
        self.messages.append(message)
        return "250 OK"

    def authenticate(
        self,
        server: SMTP,
        session: SmtpSession,
        envelope: Envelope,
        mechanism: str,
        auth_data: LoginPassword,
    ) -> AuthResult:
        self.logins.append((auth_data.login.decode(), auth_data.password.decode()))
        return AuthResult(success=True)


@pytest.fixture
def smtp_recorder() -> SmtpRecorder:
    return SmtpRecorder()


@pytest.fixture
async def smtp_settings(
    settings: Settings, smtp_recorder: SmtpRecorder
) -> AsyncIterator[Settings]:
    """Settings that reach a local SMTP server with no TLS, which `smtp_recorder` reads."""
    # The server shares the event loop of the test, so a test needs no thread.
    server = await asyncio.get_running_loop().create_server(
        lambda: SMTP(
            smtp_recorder,
            authenticator=smtp_recorder.authenticate,
            auth_require_tls=False,
        ),
        host="127.0.0.1",
        port=0,
    )
    yield settings.model_copy(
        update={
            "smtp_host": "127.0.0.1",
            "smtp_port": server.sockets[0].getsockname()[1],
            "smtp_security": SmtpSecurity.NONE,
        }
    )
    server.close()
    await server.wait_closed()


@pytest.fixture
async def signed_in_client(
    app: FastAPI,
    settings: Settings,
    db_session: AsyncSession,
    user: User,
    csrf_token: str,
) -> AsyncIterator[httpx.AsyncClient]:
    # The Session goes straight into the repository, so no test pays for argon2.
    token = SessionToken.generate(nbytes=settings.session_token_bytes)
    sessions = SqlSessionRepository(db_session)
    await sessions.add(
        Session.start(
            id=await sessions.next_id(),
            user_id=user.id,
            token=token,
            at=datetime.now(UTC),
            lifetime=settings.session_lifetime,
        )
    )
    await db_session.commit()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://testserver",
        cookies={
            settings.session_cookie_name: token.root.get_secret_value(),
            settings.csrf_cookie_name: csrf_token,
        },
        headers={settings.csrf_header_name: csrf_token},
    ) as client:
        yield client
