import json
from dataclasses import dataclass, fields
from typing import Self

from rastro.base.dto import DTO
from rastro.base.traits import FromStr


@dataclass(frozen=True)
class SignUpInput(DTO, FromStr):
    username: str
    email: str
    password: str

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class SignInInput(DTO, FromStr):
    query: str
    password: str

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class RequestPasswordResetInput(DTO, FromStr):
    email: str

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class ResetPasswordInput(DTO, FromStr):
    user_id: int
    token: str
    new_password: str

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class RequestEmailVerificationInput(DTO, FromStr):
    user_id: int

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class VerifyEmailInput(DTO, FromStr):
    user_id: int
    token: str

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class GetUserInput(DTO, FromStr):
    user_id: int

    @classmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore[misc]
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore[misc]


@dataclass(frozen=True)
class UserOutput(DTO):
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
