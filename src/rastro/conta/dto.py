from dataclasses import dataclass

from rastro.base.serialization import sanitize_email, sanitize_string, sanitize_username
from rastro.conta.entities import Conta
from rastro.conta.value_objects import Email, Name, Username


@dataclass(frozen=True)
class EntrarInput:
    query: str
    password: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "EntrarInput":
        query = data.get("query")
        password = data.get("password")
        return cls(
            query=sanitize_string(query if isinstance(query, str) else ""),
            password=password if isinstance(password, str) else "",
        )


@dataclass(frozen=True)
class CadastrarInput:
    first_name: Name
    last_name: Name
    username: Username
    email: Email
    password: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "CadastrarInput":
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        return cls(
            first_name=Name(
                sanitize_string(
                    first_name if isinstance(first_name, str) else "", max_length=100
                )
            ),
            last_name=Name(
                sanitize_string(
                    last_name if isinstance(last_name, str) else "", max_length=100
                )
            ),
            username=Username(
                sanitize_username(username if isinstance(username, str) else "")
            ),
            email=Email(sanitize_email(email if isinstance(email, str) else "")),
            password=password if isinstance(password, str) else "",
        )


@dataclass(frozen=True)
class ContaOutput:
    id: int
    username: str
    email: str
    first_name: str
    last_name: str

    @classmethod
    def from_entity(cls, entity: Conta) -> "ContaOutput":
        return cls(
            id=entity.id.value if entity.id else 0,
            username=entity.username.value,
            email=entity.email.value,
            first_name=entity.first_name.value,
            last_name=entity.last_name.value,
        )
