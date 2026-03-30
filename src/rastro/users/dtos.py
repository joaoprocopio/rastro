from dataclasses import dataclass


@dataclass(frozen=True)
class SignInInput:
    query: str
    password: str


@dataclass(frozen=True)
class SignUpInput:
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class UserOutput:
    id: int
    email: str
    username: str
    password: str
