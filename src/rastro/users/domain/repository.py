from abc import ABC, abstractmethod

from rastro.base.entity import Id
from rastro.users.domain.entities import User
from rastro.users.domain.value_objects import Email, RawPassword, Username


class UserRepository(ABC):
    @abstractmethod
    def create(
        self, username: Username, email: Email, raw_password: RawPassword
    ) -> User: ...

    @abstractmethod
    def get_by_id(self, id: Id) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: Username) -> User | None: ...
