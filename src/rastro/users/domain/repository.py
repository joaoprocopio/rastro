from abc import ABC, abstractmethod

from rastro.users.domain.aggregates import User
from rastro.users.domain.value_objects import Email, Username


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: Username) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> User: ...

    @abstractmethod
    def delete(self, user: User) -> None: ...

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool: ...

    @abstractmethod
    def exists_by_username(self, username: Username) -> bool: ...
