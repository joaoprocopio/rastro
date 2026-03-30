from dataclasses import dataclass

from rastro.conta.dto import ContaOutput
from rastro.conta.entities import Conta


def present_conta(entity: Conta) -> ContaOutput:
    return ContaOutput(
        id=entity.id.value if entity.id else 0,
        username=entity.username.value,
        email=entity.email.value,
        first_name=entity.first_name.value,
        last_name=entity.last_name.value,
        password=entity.password_hash.value,
    )


@dataclass(frozen=True)
class ContaPublic:
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
