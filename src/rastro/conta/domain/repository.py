from abc import ABC, abstractmethod
from typing import Optional

from rastro.conta.domain.aggregates import Conta
from rastro.conta.domain.value_objects import DisplayName, Email, HashedPassword
from rastro_shared_kernel.value_objects import Id


class ContaRepository(ABC):
    @abstractmethod
    def create(
        self, display_name: DisplayName, email: Email, hashed_password: HashedPassword
    ) -> Conta: ...

    @abstractmethod
    def get_by_id(self, id: Id) -> Optional[Conta]: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[Conta]: ...

    @abstractmethod
    def update_password(self, conta: Conta) -> Conta: ...
