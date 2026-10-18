from rastro.iam.application.dtos import IdentityOutputDTO, IdentityPublicDTO
from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.values import HashedPassword
from rastro.iam.models import Identity
from rastro_base.mapper import Mapper
from rastro_shared_kernel.value_objects import Id


class HydrateIdentityMapper(Mapper[Identity, IdentityAggregate]):
    @staticmethod
    def map(identity: Identity) -> IdentityAggregate:
        return IdentityAggregate(
            id=Id(identity.pk),
            email=identity.email,
            password=HashedPassword(identity.password),
            display_name=identity.display_name,
            created_at=identity.created_at,
            last_login=identity.last_login,
            is_superuser=identity.is_superuser,
            is_staff=identity.is_staff,
            is_active=identity.is_active,
        )


class DehydrateIdentityMapper(Mapper[IdentityAggregate, Identity]):
    @staticmethod
    def map(identity: IdentityAggregate) -> Identity:
        return Identity(
            id=identity.id.root,
            email=identity.email,
            password=identity.password.value,
            display_name=identity.display_name,
            created_at=identity.created_at,
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
            created_at=source.created_at,
            last_login=source.last_login,
            is_superuser=source.is_superuser,
            is_staff=source.is_staff,
            is_active=source.is_active,
        )
