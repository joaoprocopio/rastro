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
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.ports import PasswordHasher
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
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
from rastro.common.domain.value_objects import Id
from rastro.settings import Settings, SmtpPort, SmtpSecurity


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


async def _committed_reset_token(
    db_session: AsyncSession,
    *,
    user: User,
    token: ResetToken,
    at: datetime,
    lifetime: ResetTokenLifetime,
) -> ResetToken:
    reset_tokens = SqlResetTokenRepository(db_session)
    await reset_tokens.replace(
        IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=user.id,
            token=token,
            at=at,
            lifetime=lifetime,
        )
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
        lifetime=settings.reset_token_lifetime,
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
        lifetime=settings.reset_token_lifetime,
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
