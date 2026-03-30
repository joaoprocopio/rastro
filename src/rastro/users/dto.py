from dataclasses import dataclass


@dataclass(frozen=True)
class SignInInput:
    query: str
    password: str


@dataclass(frozen=True)
class SignUpInput:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class UserOutput:
    id: int
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
