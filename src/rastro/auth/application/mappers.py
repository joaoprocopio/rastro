from rastro.auth.application.dtos import SessionGetOutput
from rastro.auth.domain.aggregates import User


def session_get_output(user: User) -> SessionGetOutput:
    return SessionGetOutput(email=user.email, display_name=user.display_name)
