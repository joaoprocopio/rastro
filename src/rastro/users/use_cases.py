from django.contrib.auth.hashers import check_password, make_password

from rastro.base.use_cases import UseCase
from rastro.users.dto import SignInInput, SignUpInput, UserOutput
from rastro.users.entities import User
from rastro.users.errors import (
    AuthenticationError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from rastro.users.repository import UserRepository
from rastro.users.value_objects import PasswordHash


class SignUpUseCase(UseCase[SignUpInput, UserOutput]):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, input: SignUpInput) -> UserOutput:
        if self.repository.get_by_email(input.email.value):
            raise EmailAlreadyExistsError(f"Email already exists: {email.value}")

        if self.repository.get_by_username(username.value):
            raise UsernameAlreadyExistsError(
                f"Username already exists: {username.value}"
            )

        password_hash = PasswordHash(make_password(password))

        user = User(
            id=None,
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )

        saved_user = self.repository.save(user)
        return present_user(saved_user)


class SignInUseCase(UseCase[SignInInput, UserOutput]):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, input: SignInInput) -> UserOutput:
        query, password = schema_to_entrar_input(input)

        user = self.repository.get_by_email(query)
        if user is None:
            user = self.repository.get_by_username(query)

        if user is None:
            raise AuthenticationError("Invalid credentials")

        if not check_password(password, user.password_hash.value):
            raise AuthenticationError("Invalid credentials")

        return present_user(user)
