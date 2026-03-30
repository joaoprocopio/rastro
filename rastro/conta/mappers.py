from django.contrib.auth.models import User

from rastro.base.entities import Id
from rastro.base.mappers import Mapper
from rastro.conta.entities import Conta
from rastro.conta.schema import CadastrarSchema, EntrarSchema
from rastro.conta.value_objects import Email, Name, PasswordHash, Username


class ContaMapper(Mapper[Conta, User]):
    def to_source(self, input: Conta) -> User:
        return User()

    def to_target(self, model: User) -> Conta:
        return Conta(
            id=Id(model.pk),
            email=Email(model.email),
            first_name=Name(model.first_name),
            last_name=Name(model.last_name),
            password_hash=PasswordHash(model.password),
            username=Username(model.username),
        )


def schema_to_entrar_input(schema: EntrarSchema) -> tuple[str, str]:
    return schema.query, schema.password


def schema_to_cadastrar_values(
    schema: CadastrarSchema,
) -> tuple[Name, Name, Username, Email, str]:
    return (
        Name(schema.first_name),
        Name(schema.last_name),
        Username(schema.username),
        Email(schema.email),
        schema.password,
    )
