from typing import Optional

from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.repository import IdentityRepository
from rastro.iam.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
)
from rastro.iam.models import IdentityModel
from rastro.iam.shared.mappers import DehydrateIdentityMapper, HydrateIdentityMapper
from rastro_shared_kernel.value_objects import Id


class DjangoIdentityRepository(IdentityRepository):
    def create(
        self, display_name: DisplayName, email: Email, hashed_password: HashedPassword
    ) -> IdentityAggregate:
        identity_model = IdentityModel.objects.create(
            display_name=display_name.root,
            email=email.root,
            password=hashed_password.root,
        )
        identity_model.save()
        identity_model.refresh_from_db()

        return HydrateIdentityMapper.map(identity_model)

    def get_by_id(self, id: Id) -> Optional[IdentityAggregate]:
        try:
            identity_model = IdentityModel.objects.get(pk=id.root)

            return HydrateIdentityMapper.map(identity_model)
        except IdentityModel.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> Optional[IdentityAggregate]:
        try:
            identity_model = IdentityModel.objects.get(email=email.root)

            return HydrateIdentityMapper.map(identity_model)
        except IdentityModel.DoesNotExist:
            return None

    def update_password(self, identity: IdentityAggregate) -> IdentityAggregate:
        identity_model = DehydrateIdentityMapper.map(identity)
        identity_model.save(update_fields=["password"])

        return HydrateIdentityMapper.map(identity_model)
