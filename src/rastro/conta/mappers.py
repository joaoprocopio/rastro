from django.contrib.auth.models import User

from rastro.base.entities import Id
from rastro.base.mappers import Mapper
from rastro.conta.entities import Conta
from rastro.conta.value_objects import Email, Name, PasswordHash, Username


class ContaMapper(Mapper[User, Conta]):
    @staticmethod
    def to_target(input: Conta) -> User:
        return User(
            id=input.id.value,  # type: ignore
            username=input.username.value,
            email=input.email.value,
            password=input.password_hash.value,
            first_name=input.first_name.value,
            last_name=input.last_name.value,
        )

    @staticmethod
    def to_source(model: User) -> Conta:
        return Conta(
            id=Id(model.pk),
            email=Email(model.email),
            first_name=Name(model.first_name),
            last_name=Name(model.last_name),
            password_hash=PasswordHash(model.password),
            username=Username(model.username),
        )
