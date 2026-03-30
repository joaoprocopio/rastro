from dataclasses import dataclass

from rastro.base.dto import DTO


@dataclass(frozen=True)
class SignUpInput(DTO):
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class SignInInput(DTO):
    query: str
    password: str


@dataclass(frozen=True)
class GetUserInput(DTO):
    user_id: int


@dataclass(frozen=True)
class UserOutput(DTO):
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
