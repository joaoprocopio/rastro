from abc import ABC, abstractmethod
from typing import Optional

from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.value_objects import DisplayName, Email, HashedPassword
from rastro_shared_kernel.value_objects import Id


class IdentityRepository(ABC):
    @abstractmethod
    def create(
        self, display_name: DisplayName, email: Email, hashed_password: HashedPassword
    ) -> IdentityAggregate: ...

    @abstractmethod
    def get_by_id(self, id: Id) -> Optional[IdentityAggregate]: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[IdentityAggregate]: ...

    @abstractmethod
    def update_password(self, identity: IdentityAggregate) -> IdentityAggregate: ...
