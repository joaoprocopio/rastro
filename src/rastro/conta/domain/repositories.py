from typing import Protocol

from .entities import User


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_username(self, username: str) -> User | None: ...
    def create(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
    ) -> User: ...
    def verify_password(self, user: User, password: str) -> bool: ...
