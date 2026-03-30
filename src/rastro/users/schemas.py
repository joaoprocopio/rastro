from dataclasses import dataclass

from rastro.base.serialization import sanitize_email, sanitize_string, sanitize_username


@dataclass(frozen=True)
class EntrarSchema:
    query: str
    password: str

    @classmethod
    def from_request(cls, data: dict[str, object]) -> "EntrarSchema":
        query = data.get("query")
        password = data.get("password")
        return cls(
            query=sanitize_string(query if isinstance(query, str) else ""),
            password=password if isinstance(password, str) else "",
        )


@dataclass(frozen=True)
class CadastrarSchema:
    username: str
    email: str
    password: str

    @classmethod
    def from_request(cls, data: dict[str, object]) -> "CadastrarSchema":

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        return cls(
            username=sanitize_username(username if isinstance(username, str) else ""),
            email=sanitize_email(email if isinstance(email, str) else ""),
            password=password if isinstance(password, str) else "",
        )
