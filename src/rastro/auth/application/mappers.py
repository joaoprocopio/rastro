from rastro.auth.application.dtos import SessionGetOutput, SessionStartOutput
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import SessionToken


def session_start_output(
    session: Session, *, token: SessionToken
) -> SessionStartOutput:
    return SessionStartOutput(token=token, expires_at=session.expires_at)


def session_get_output(user: User) -> SessionGetOutput:
    return SessionGetOutput(email=user.email, display_name=user.display_name)
