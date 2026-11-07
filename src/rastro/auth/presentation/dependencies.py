from functools import cache

from procrastinate import JobContext

from rastro.auth.domain.ports import (
    Clock,
    EmailSender,
    PasswordHasher,
    ResetTokenRepository,
    SessionRepository,
    UserRepository,
)
from rastro.auth.infrastructure.adapters import (
    Argon2PasswordHasher,
    SmtpEmailSender,
    SystemClock,
)
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.common.presentation.dependencies import DatabaseSession
from rastro.settings import Settings

JOB_EMAIL_SENDER_KEY = "email_sender"


# One instance per process, so the fixed hash of an unknown email is computed once.
@cache
def password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def clock() -> Clock:
    return SystemClock()


def user_repository(db_session: DatabaseSession) -> UserRepository:
    return SqlUserRepository(db_session)


def session_repository(db_session: DatabaseSession) -> SessionRepository:
    return SqlSessionRepository(db_session)


def reset_token_repository(db_session: DatabaseSession) -> ResetTokenRepository:
    return SqlResetTokenRepository(db_session)


def email_sender(settings: Settings) -> EmailSender:
    return SmtpEmailSender(settings)


def job_email_sender(context: JobContext) -> EmailSender:
    sender: EmailSender = context.additional_context[JOB_EMAIL_SENDER_KEY]
    return sender
