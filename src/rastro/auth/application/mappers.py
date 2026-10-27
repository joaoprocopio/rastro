from rastro.auth.application.dtos import UserGetCurrentOutput
from rastro.auth.domain.aggregates import User


def user_get_current_output_from_user(user: User) -> UserGetCurrentOutput:
    return UserGetCurrentOutput(email=user.email, display_name=user.display_name)
