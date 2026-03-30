from abc import abstractmethod

from rastro.base import DomainService
from rastro.users.domain.aggregates import User
from rastro.users.domain.value_objects import HashedPassword, Password


class PasswordHashingService(DomainService):
    @abstractmethod
    def hash_password(self, password: Password) -> HashedPassword: ...

    @abstractmethod
    def verify_password(
        self, password: Password, hashed_password: HashedPassword
    ) -> bool: ...


class AuthenticationService(DomainService):
    @abstractmethod
    def authenticate(self, user: User, password: Password) -> bool: ...

    @abstractmethod
    def login(self, user: User) -> str: ...

    @abstractmethod
    def logout(self, user: User) -> None: ...


class EmailService(DomainService):
    @abstractmethod
    def send_verification_email(self, user: User, token: str) -> None: ...

    @abstractmethod
    def send_password_reset_email(self, user: User, token: str) -> None: ...


class TokenService(DomainService):
    @abstractmethod
    def generate_verification_token(self, user: User) -> str: ...

    @abstractmethod
    def generate_password_reset_token(self, user: User) -> str: ...

    @abstractmethod
    def verify_token(self, token: str, token_type: str) -> int | None: ...
