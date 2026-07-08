from abc import abstractmethod
from typing import TYPE_CHECKING, NamedTuple, Optional

from rastro_base.service import Service

if TYPE_CHECKING:  # prevents circular imports
    from rastro.iam.domain.aggregates import IdentityAggregate
    from rastro.iam.domain.value_objects import HashedPassword, RawPassword


class PasswordVerification(NamedTuple):
    is_correct: bool
    must_upgrade: bool


class PasswordHashingService(Service):
    @abstractmethod
    def hash(self, raw_password: RawPassword) -> HashedPassword: ...

    @abstractmethod
    def verify(
        self, raw_password: RawPassword, hashed_password: HashedPassword
    ) -> PasswordVerification: ...


class SessionService(Service):
    @abstractmethod
    def start(self, identity: IdentityAggregate) -> None: ...

    @abstractmethod
    def end(self) -> None: ...

    @abstractmethod
    def current_identity(self) -> Optional[IdentityAggregate]: ...
