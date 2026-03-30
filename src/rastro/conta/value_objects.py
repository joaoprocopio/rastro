import re

from rastro.base.value_objects import ValueObject
from rastro.conta.errors import (
    InvalidEmailError,
    InvalidNameError,
    InvalidPasswordError,
    InvalidUsernameError,
)


class Email(ValueObject[str]):
    def validate(self) -> None:
        if not self.value:
            raise InvalidEmailError("Email cannot be empty")
        if "@" not in self.value:
            raise InvalidEmailError(f"Invalid email format: {self.value}")
        local, _, domain = self.value.partition("@")
        if not local or not domain:
            raise InvalidEmailError(f"Invalid email format: {self.value}")


class Username(ValueObject[str]):
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

    def validate(self) -> None:
        if not self.value:
            raise InvalidUsernameError("Username cannot be empty")
        if len(self.value) > 50:
            raise InvalidUsernameError("Username cannot exceed 50 characters")
        if not self.USERNAME_PATTERN.match(self.value):
            raise InvalidUsernameError(
                "Username can only contain alphanumeric characters and underscores"
            )


class Name(ValueObject[str]):
    def validate(self) -> None:
        if not self.value:
            raise InvalidNameError("Name cannot be empty")
        if len(self.value) > 100:
            raise InvalidNameError("Name cannot exceed 100 characters")


class PasswordHash(ValueObject[str]):
    def validate(self) -> None:
        if not self.value:
            raise InvalidPasswordError("Password hash cannot be empty")


class Password(ValueObject[str]):
    MIN_LENGTH = 8

    def validate(self) -> None:
        if not self.value:
            raise InvalidPasswordError("Password cannot be empty")
        if len(self.value) < self.MIN_LENGTH:
            raise InvalidPasswordError(
                f"Password must be at least {self.MIN_LENGTH} characters"
            )
