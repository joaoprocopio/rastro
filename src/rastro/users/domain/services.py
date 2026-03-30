from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

from rastro.base.domain_service import DomainService
from rastro.base.entity import Id
from rastro.users.domain.value_objects import HashedPassword, RawPassword


class PasswordHashingService(DomainService):
    @abstractmethod
    def hash(self, raw_password: RawPassword) -> HashedPassword: ...

    @abstractmethod
    def verify(
        self, raw_password: RawPassword, hashed_password: HashedPassword
    ) -> bool: ...


class SessionService(DomainService):
    @abstractmethod
    def login(self, request: "HttpRequest", user_id: Id) -> None: ...

    @abstractmethod
    def logout(self, request: "HttpRequest") -> None: ...

    @abstractmethod
    def access_current_user_id(self, request: "HttpRequest") -> Id | None: ...
