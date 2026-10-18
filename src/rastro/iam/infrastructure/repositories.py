from typing import Optional

from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.repository import IdentityRepository
from rastro.iam.values import (
    DisplayName,
    Email,
    HashedPassword,
)
from rastro.iam.models import Identity
from rastro.iam.shared.mappers import HydrateIdentityMapper
from rastro_shared_kernel.value_objects import Id


class DjangoIdentityRepository(IdentityRepository):
    def create(
        self, display_name: DisplayName, email: Email, hashed_password: HashedPassword
    ) -> IdentityAggregate:
        identity_model = Identity.objects.create(
            display_name=display_name,
            email=email,
            password=hashed_password.value,
        )
        identity_model.save()
        identity_model.refresh_from_db()

        return HydrateIdentityMapper.map(identity_model)

    def get_by_id(self, id: Id) -> Optional[IdentityAggregate]:
        try:
            identity_model = Identity.objects.get(pk=id.root)

            return HydrateIdentityMapper.map(identity_model)
        except Identity.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> Optional[IdentityAggregate]:
        try:
            identity_model = Identity.objects.get(email=email)

            return HydrateIdentityMapper.map(identity_model)
        except Identity.DoesNotExist:
            return None
