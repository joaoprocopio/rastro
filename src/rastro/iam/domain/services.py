from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from rastro_base.service import Service

if TYPE_CHECKING:  # prevents circular imports
    from rastro.iam.domain.aggregates import IdentityAggregate
    from rastro.iam.values import HashedPassword, RawPassword


class PasswordHashingService(Service):
    @abstractmethod
    def hash(self, raw_password: RawPassword) -> HashedPassword: ...


class SessionService(Service):
    @abstractmethod
    def start(self, identity: IdentityAggregate) -> None: ...

    @abstractmethod
    def end(self) -> None: ...

    @abstractmethod
    def current_identity(self) -> Optional[IdentityAggregate]: ...
