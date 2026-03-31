from abc import ABC, abstractmethod
from typing import Optional

from rastro.auth.domain.entities import User
from rastro.auth.domain.value_objects import Email, HashedPassword, Username
from rastro_base.entity import Id


class UserRepository(ABC):
    @abstractmethod
    def create(
        self, username: Username, email: Email, hashed_password: HashedPassword
    ) -> User: ...

    @abstractmethod
    def get_by_id(self, id: Id) -> Optional[User]: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[User]: ...

    @abstractmethod
    def get_by_username(self, username: Username) -> Optional[User]: ...
