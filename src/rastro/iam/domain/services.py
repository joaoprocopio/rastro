from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from rastro_base.service import Service

if TYPE_CHECKING:  # prevents circular imports
    from rastro.iam.domain.aggregates import IdentityAggregate


class SessionService(Service):
    @abstractmethod
    def start(self, identity: IdentityAggregate) -> None: ...

    @abstractmethod
    def end(self) -> None: ...

    @abstractmethod
    def current_identity(self) -> Optional[IdentityAggregate]: ...
