from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    query: str
    password: str
