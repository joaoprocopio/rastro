from dataclasses import dataclass


@dataclass(frozen=True)
class EntrarInput:
    query: str
    password: str


@dataclass(frozen=True)
class CadastrarInput:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class ContaOutput:
    id: int
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
