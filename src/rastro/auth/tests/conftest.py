import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from email import message_from_bytes, policy
from email.message import EmailMessage
from enum import StrEnum

import httpx
import pytest
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, LoginPassword
from aiosmtpd.smtp import Session as SmtpSession
from fastapi import FastAPI
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.testing import InMemoryConnector
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.api_app import create_api_app
from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.ports import PasswordHasher
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    OutgoingEmail,
    RawPassword,
    ResetLinkUrl,
    ResetToken,
    ResetTokenLifetime,
    SessionToken,
)
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.presentation import dependencies
from rastro.auth.presentation.tasks import (
    PASSWORD_RESET_QUEUE,
    password_reset_send_task,
)
from rastro.common.domain.value_objects import Id
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.settings import Settings, SmtpPort, SmtpSecurity

STATEMENTS_THAT_WAIT = text(
    "SELECT count(*) FROM pg_stat_activity"
    " WHERE datname = current_database()"
    " AND wait_event_type = 'Lock' AND query LIKE :statement"
)


async def until_a_statement_waits(probe: AsyncSession, *, statement: str) -> None:
    async with asyncio.timeout(5):
        while not await probe.scalar(STATEMENTS_THAT_WAIT, {"statement": statement}):
            await probe.rollback()


@pytest.fixture
def connector(worker_app: App) -> InMemoryConnector:
    """The connector of `worker_app`, whose job rows a test reads and makes due."""
    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)
    return connector


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
async def committed_user(engine: AsyncEngine) -> AsyncIterator[User]:
    """A User that every connection sees, which the test does not roll back."""
    sessionmaker = create_sessionmaker(engine)
    async with sessionmaker.begin() as db_session:
        users = SqlUserRepository(db_session)
        user = User(
            id=await users.next_id(),
            email=Email("committed@x.com"),
            display_name=DisplayName("Committed"),
            hashed_password=HashedPassword("fake$password"),
        )
        await users.add(user)

    yield user

    # The foreign key deletes each Session and the Reset token with their User.
    async with sessionmaker.begin() as db_session:
        await db_session.execute(
            text("DELETE FROM auth_user WHERE id = :id"), {"id": user.id.root}
        )


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


async def _committed_reset_token(
    db_session: AsyncSession,
    *,
    user: User,
    token: ResetToken,
    at: datetime,
    settings: Settings,
) -> ResetToken:
    reset_tokens = SqlResetTokenRepository(db_session)
    await reset_tokens.replace_after_cooldown(
        IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=user.id,
            token=token,
            at=at,
            lifetime=settings.reset_token_lifetime,
        ),
        cooldown=settings.reset_token_cooldown,
    )
    await db_session.commit()
    return token


@pytest.fixture
async def reset_token(
    db_session: AsyncSession, user: User, settings: Settings
) -> ResetToken:
    """The token of a committed Reset token of `user`, issued now by the wall clock."""
    return await _committed_reset_token(
        db_session,
        user=user,
        token=ResetToken(SecretStr("reset")),
        at=datetime.now(UTC),
        settings=settings,
    )


@pytest.fixture
async def expired_reset_token(
    db_session: AsyncSession, user: User, settings: Settings
) -> ResetToken:
    """The token of a committed Reset token of `user` whose lifetime runs out now."""
    return await _committed_reset_token(
        db_session,
        user=user,
        token=ResetToken(SecretStr("expired")),
        at=datetime.now(UTC) - settings.reset_token_lifetime.root,
        settings=settings,
    )


@pytest.fixture
def one_hour_reset_token() -> IssuedResetToken:
    """A Reset token in no repository, with a lifetime of one hour."""
    return IssuedResetToken.issue(
        id=Id(1),
        user_id=Id(2),
        token=ResetToken(SecretStr("token")),
        at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        lifetime=ResetTokenLifetime(timedelta(hours=1)),
    )


@pytest.fixture
def password_reset_email() -> OutgoingEmail:
    """The email to `ana@x.com` with the token `abc` and a link that works for one hour."""
    return OutgoingEmail.password_reset(
        to=Email("ana@x.com"),
        link_url=ResetLinkUrl("https://rastro.example/password-reset"),
        token=ResetToken(SecretStr("abc")),
        lifetime=ResetTokenLifetime(timedelta(hours=1)),
    )


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
    await reset_tokens.replace_after_cooldown(
        reset_token, cooldown=settings.reset_token_cooldown
    )
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
            "smtp_port": SmtpPort(server.sockets[0].getsockname()[1]),
            "smtp_security": SmtpSecurity.NONE,
        }
    )
    server.close()
    await server.wait_closed()


class SmtpFault(StrEnum):
    """What `SmtpScript` does at a step in place of a reply."""

    CLOSE = "close"
    SILENCE = "silence"
    BAD_TLS = "bad_tls"


class SmtpScript:
    """The handler of `scripted_smtp_settings`, whose `replies` a test sets for each step."""

    def __init__(self) -> None:
        self.replies: dict[str, str | SmtpFault] = {
            "GREETING": "220 Ready",
            "EHLO": "250-test\r\n250-AUTH PLAIN\r\n250 STARTTLS",
            "HELO": "250 OK",
            "AUTH": "235 OK",
            "STARTTLS": "220 Go",
            "MAIL": "250 OK",
            "RCPT": "250 OK",
            "DATA": "354 Go",
            "BODY": "250 OK",
            "RSET": "250 OK",
            "QUIT": "221 Bye",
        }

    async def handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            await self._converse(reader, writer)
        except ConnectionError:
            pass
        finally:
            writer.close()

    async def _converse(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        if not await self._answer("GREETING", reader, writer):
            return
        while line := await reader.readline():
            step = line.split()[0].decode().upper()
            if not await self._answer(step, reader, writer) or step == "QUIT":
                return
            if step == "DATA" and self.replies[step] == "354 Go":
                await reader.readuntil(b"\r\n.\r\n")
                if not await self._answer("BODY", reader, writer):
                    return

    async def _answer(
        self, step: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bool:
        reply = self.replies[step]
        match reply:
            case SmtpFault.CLOSE:
                return False
            case SmtpFault.SILENCE:
                # The read ends when the client gives up and closes the connection.
                await reader.read()
                return False
            case SmtpFault.BAD_TLS:
                writer.write(b"220 Go\r\n")
                await writer.drain()
                await reader.read(1)
                writer.write(b"not a TLS record\r\n")
                await writer.drain()
                return False
            case _:
                writer.write(f"{reply}\r\n".encode())
                await writer.drain()
                return True


@pytest.fixture
def smtp_script() -> SmtpScript:
    return SmtpScript()


@pytest.fixture
async def scripted_smtp_settings(
    settings: Settings, smtp_script: SmtpScript
) -> AsyncIterator[Settings]:
    """Settings that reach a local SMTP server, which answers as `smtp_script` says."""
    server = await asyncio.start_server(smtp_script.handle, host="127.0.0.1", port=0)
    yield settings.model_copy(
        update={
            "smtp_host": "127.0.0.1",
            "smtp_port": SmtpPort(server.sockets[0].getsockname()[1]),
            "smtp_security": SmtpSecurity.NONE,
        }
    )
    server.close()
    await server.wait_closed()


@pytest.fixture
async def committing_client(
    engine: AsyncEngine,
    settings: Settings,
    csrf_token: str,
    password_hasher: PasswordHasher,
) -> AsyncIterator[httpx.AsyncClient]:
    """A client whose requests each commit on their own connection, as in production."""
    app = create_api_app(settings=settings, sessionmaker=create_sessionmaker(engine))
    app.dependency_overrides[dependencies.password_hasher] = lambda: password_hasher
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="https://testserver",
        cookies={settings.csrf_cookie_name: csrf_token},
        headers={settings.csrf_header_name: csrf_token},
    ) as client:
        yield client


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
