from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class AuthenticateUserInput:
    query: str
    password: str


@dataclass(frozen=True)
class CreateUserInput:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class UserOutput(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
