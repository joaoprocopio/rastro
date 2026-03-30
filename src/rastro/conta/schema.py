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
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

    @classmethod
    def from_request(cls, data: dict[str, object]) -> "CadastrarSchema":
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        return cls(
            first_name=sanitize_string(
                first_name if isinstance(first_name, str) else "", max_length=100
            ),
            last_name=sanitize_string(
                last_name if isinstance(last_name, str) else "", max_length=100
            ),
            username=sanitize_username(username if isinstance(username, str) else ""),
            email=sanitize_email(email if isinstance(email, str) else ""),
            password=password if isinstance(password, str) else "",
        )
