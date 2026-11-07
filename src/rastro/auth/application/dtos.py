from datetime import datetime

from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    RawPassword,
    ResetToken,
    SessionToken,
)
from rastro.common.application.dtos import DTO


class UserRegisterInput(DTO):
    email: Email
    display_name: DisplayName
    password: RawPassword


class SessionStartInput(DTO):
    email: Email
    password: RawPassword


class SessionStartOutput(DTO):
    token: SessionToken
    expires_at: datetime


class SessionGetOutput(DTO):
    email: Email
    display_name: DisplayName


class SessionRemoveExpiredOutput(DTO):
    count: int


class PasswordResetRequestInput(DTO):
    email: Email


class PasswordResetSendInput(DTO):
    email: Email


class PasswordResetConfirmInput(DTO):
    token: ResetToken
    password: RawPassword
