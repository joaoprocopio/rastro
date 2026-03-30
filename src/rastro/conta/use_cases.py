from django.contrib.auth.hashers import check_password, make_password

from rastro.base.errors import (
    AuthenticationError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from rastro.conta.dto import CadastrarInput, ContaOutput, EntrarInput
from rastro.conta.entities import Conta
from rastro.conta.repository import ContaRepository
from rastro.conta.value_objects import PasswordHash


class CadastrarUseCase:
    def __init__(self, repository: ContaRepository):
        self.repository = repository

    def execute(self, input_dto: CadastrarInput) -> ContaOutput:
        if self.repository.get_by_email(input_dto.email.value):
            raise EmailAlreadyExistsError(
                f"Email already exists: {input_dto.email.value}"
            )

        if self.repository.get_by_username(input_dto.username.value):
            raise UsernameAlreadyExistsError(
                f"Username already exists: {input_dto.username.value}"
            )

        password_hash = PasswordHash(make_password(input_dto.password))

        conta = Conta(
            id=None,
            username=input_dto.username,
            email=input_dto.email,
            password_hash=password_hash,
            first_name=input_dto.first_name,
            last_name=input_dto.last_name,
        )

        saved_conta = self.repository.save(conta)
        return ContaOutput.from_entity(saved_conta)


class EntrarUseCase:
    def __init__(self, repository: ContaRepository):
        self.repository = repository

    def execute(self, input_dto: EntrarInput) -> ContaOutput:
        conta = self.repository.get_by_email(input_dto.query)
        if conta is None:
            conta = self.repository.get_by_username(input_dto.query)

        if conta is None:
            raise AuthenticationError("Invalid credentials")

        if not check_password(input_dto.password, conta.password_hash.value):
            raise AuthenticationError("Invalid credentials")

        return ContaOutput.from_entity(conta)
