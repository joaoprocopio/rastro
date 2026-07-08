from rastro.iam.application.dtos import IdentityOutputDTO, IdentityPublicDTO
from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.value_objects import DisplayName, Email, HashedPassword
from rastro.iam.models import IdentityModel
from rastro_base.mapper import Mapper
from rastro_shared_kernel.value_objects import Id


class HydrateIdentityMapper(Mapper[IdentityModel, IdentityAggregate]):
    @staticmethod
    def map(identity: IdentityModel) -> IdentityAggregate:
        return IdentityAggregate(
            id=Id(identity.pk),
            email=Email(identity.email),
            password=HashedPassword(identity.password),
            display_name=DisplayName(identity.display_name),
            date_joined=identity.date_joined,
            last_login=identity.last_login,
            is_superuser=identity.is_superuser,
            is_staff=identity.is_staff,
            is_active=identity.is_active,
        )


class DehydrateIdentityMapper(Mapper[IdentityAggregate, IdentityModel]):
    @staticmethod
    def map(identity: IdentityAggregate) -> IdentityModel:
        return IdentityModel(
            id=identity.id.root,
            email=identity.email.root,
            password=identity.password.root,
            display_name=identity.display_name.root,
            date_joined=identity.date_joined,
            last_login=identity.last_login,
            is_superuser=identity.is_superuser,
            is_staff=identity.is_staff,
            is_active=identity.is_active,
        )


class PresentIdentityMapper(
    Mapper[IdentityAggregate | IdentityOutputDTO, IdentityPublicDTO]
):
    @staticmethod
    def map(source: IdentityAggregate | IdentityOutputDTO) -> IdentityPublicDTO:
        match source:
            case IdentityAggregate():
                return IdentityPublicDTO(
                    display_name=source.display_name,
                    email=source.email,
                )
            case IdentityOutputDTO():
                return IdentityPublicDTO(
                    display_name=source.display_name,
                    email=source.email,
                )


class OutputIdentityMapper(Mapper[IdentityAggregate, IdentityOutputDTO]):
    @staticmethod
    def map(source: IdentityAggregate) -> IdentityOutputDTO:
        return IdentityOutputDTO(
            id=source.id,
            email=source.email,
            display_name=source.display_name,
            date_joined=source.date_joined,
            last_login=source.last_login,
            is_superuser=source.is_superuser,
            is_staff=source.is_staff,
            is_active=source.is_active,
        )
