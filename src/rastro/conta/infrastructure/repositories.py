from typing import Optional

from rastro.conta.domain.aggregates import Conta
from rastro.conta.domain.repository import ContaRepository
from rastro.conta.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
)
from rastro.conta.models import Conta as ContaModel
from rastro.conta.shared.mappers import DehydrateContaMapper, HydrateContaMapper
from rastro_shared_kernel.value_objects import Id


class DjangoContaRepository(ContaRepository):
    def create(
        self, display_name: DisplayName, email: Email, hashed_password: HashedPassword
    ) -> Conta:
        conta_model = ContaModel.objects.create(
            display_name=display_name.root,
            email=email.root,
            password=hashed_password.root,
        )
        conta_model.save()
        conta_model.refresh_from_db()

        return HydrateContaMapper.map(conta_model)

    def get_by_id(self, id: Id) -> Optional[Conta]:
        try:
            conta_model = ContaModel.objects.get(pk=id.root)

            return HydrateContaMapper.map(conta_model)
        except ContaModel.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> Optional[Conta]:
        try:
            conta_model = ContaModel.objects.get(email=email.root)

            return HydrateContaMapper.map(conta_model)
        except ContaModel.DoesNotExist:
            return None

    def update_password(self, conta: Conta) -> Conta:
        conta_model = DehydrateContaMapper.map(conta)
        conta_model.save(update_fields=["password"])

        return HydrateContaMapper.map(conta_model)
