from abc import abstractmethod
from typing import TYPE_CHECKING, NamedTuple, Optional

from rastro_base.service import Service

if TYPE_CHECKING:  # previne imports circulares
    from rastro.conta.domain.aggregates import Conta
    from rastro.conta.domain.value_objects import HashedPassword, RawPassword


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
    def login(self, conta: Conta) -> None: ...

    @abstractmethod
    def logout(self) -> None: ...

    @abstractmethod
    def logged_conta(self) -> Optional[Conta]: ...
