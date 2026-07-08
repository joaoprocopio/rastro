from rastro.conta.application.dtos import ContaOutput, ContaPublic
from rastro.conta.domain.aggregates import Conta
from rastro.conta.domain.value_objects import DisplayName, Email, HashedPassword
from rastro.conta.models import Conta as ContaModel
from rastro_base.mapper import Mapper
from rastro_shared_kernel.value_objects import Id


class HydrateContaMapper(Mapper[ContaModel, Conta]):
    @staticmethod
    def map(conta: ContaModel) -> Conta:
        return Conta(
            id=Id(conta.pk),
            email=Email(conta.email),
            password=HashedPassword(conta.password),
            display_name=DisplayName(conta.display_name),
            date_joined=conta.date_joined,
            last_login=conta.last_login,
            is_superuser=conta.is_superuser,
            is_staff=conta.is_staff,
            is_active=conta.is_active,
        )


class DehydrateContaMapper(Mapper[Conta, ContaModel]):
    @staticmethod
    def map(conta: Conta) -> ContaModel:
        return ContaModel(
            id=conta.id.root,
            email=conta.email.root,
            password=conta.password.root,
            display_name=conta.display_name.root,
            date_joined=conta.date_joined,
            last_login=conta.last_login,
            is_superuser=conta.is_superuser,
            is_staff=conta.is_staff,
            is_active=conta.is_active,
        )


class PresentContaMapper(Mapper[Conta | ContaOutput, ContaPublic]):
    @staticmethod
    def map(source: Conta | ContaOutput) -> ContaPublic:
        match source:
            case Conta():
                return ContaPublic(
                    display_name=source.display_name,
                    email=source.email,
                )
            case ContaOutput():
                return ContaPublic(
                    display_name=source.display_name,
                    email=source.email,
                )


class OutputContaMapper(Mapper[Conta, ContaOutput]):
    @staticmethod
    def map(source: Conta) -> ContaOutput:
        return ContaOutput(
            id=source.id,
            email=source.email,
            password=source.password,
            display_name=source.display_name,
            date_joined=source.date_joined,
            last_login=source.last_login,
            is_superuser=source.is_superuser,
            is_staff=source.is_staff,
            is_active=source.is_active,
        )
