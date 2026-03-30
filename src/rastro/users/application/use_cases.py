from rastro.base import UseCase
from rastro.users.application.dtos import (
    ResetPasswordInput,
    SignInInput,
    SignOutInput,
    SignUpInput,
    UserOutput,
    VerifyEmailInput,
)
from rastro.users.domain.aggregates import User
from rastro.users.domain.errors import (
    AuthenticationError,
    EmailAlreadyExistsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from rastro.users.domain.events import (
    UserEmailVerified,
    UserLoggedIn,
    UserLoggedOut,
    UserPasswordResetCompleted,
    UserPasswordResetRequested,
    UserRegistered,
)
from rastro.users.domain.repository import UserRepository
from rastro.users.domain.services import (
    PasswordHashingService,
    TokenService,
)
from rastro.users.domain.value_objects import Email, Password, Username


class SignUpUseCase(UseCase[SignUpInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
        password_hashing_service: PasswordHashingService,
    ):
        self._repository = repository
        self._password_hashing_service = password_hashing_service

    def execute(self, input: SignUpInput) -> UserOutput:
        email = Email(input.email)
        username = Username(input.username)
        password = Password(input.password)

        if self._repository.exists_by_email(email):
            raise EmailAlreadyExistsError(f"Email {input.email} already exists")

        if self._repository.exists_by_username(username):
            raise UsernameAlreadyExistsError(
                f"Username {input.username} already exists"
            )

        hashed_password = self._password_hashing_service.hash_password(password)

        user = User(
            id=None,
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
        )

        user.add_domain_event(
            UserRegistered(
                user_id=0,
                email=input.email,
                username=input.username,
            )
        )

        saved_user = self._repository.save(user)

        return UserOutput(
            id=saved_user.id.value,
            email=saved_user.email.value,
            username=saved_user.username.value,
            is_active=saved_user.is_active,
            is_verified=saved_user.is_verified,
        )


class SignInUseCase(UseCase[SignInInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
        password_hashing_service: PasswordHashingService,
    ):
        self._repository = repository
        self._password_hashing_service = password_hashing_service

    def execute(self, input: SignInInput) -> UserOutput:
        if "@" in input.query:
            user = self._repository.get_by_email(Email(input.query))
        else:
            user = self._repository.get_by_username(Username(input.query))

        if user is None:
            raise AuthenticationError("Invalid credentials")

        password = Password(input.password)

        if not self._password_hashing_service.verify_password(
            password, user.hashed_password
        ):
            raise AuthenticationError("Invalid credentials")

        user.add_domain_event(UserLoggedIn(user_id=user.id.value))

        return UserOutput(
            id=user.id.value,
            email=user.email.value,
            username=user.username.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )


class SignOutUseCase(UseCase[SignOutInput, None]):
    def __init__(self, repository: UserRepository):
        self._repository = repository

    def execute(self, input: SignOutInput) -> None:
        user = self._repository.get_by_id(input.user_id)
        if user is None:
            raise UserNotFoundError(f"User with id {input.user_id} not found")

        user.add_domain_event(UserLoggedOut(user_id=user.id.value))


class RequestPasswordResetUseCase(UseCase[None, None]):
    def __init__(
        self,
        repository: UserRepository,
        token_service: TokenService,
    ):
        self._repository = repository
        self._token_service = token_service

    def execute(self, email: str) -> str:
        user = self._repository.get_by_email(Email(email))
        if user is None:
            raise UserNotFoundError(f"User with email {email} not found")

        token = self._token_service.generate_password_reset_token(user)

        user.add_domain_event(
            UserPasswordResetRequested(
                user_id=user.id.value,
                email=user.email.value,
                token=token,
            )
        )

        return token


class ResetPasswordUseCase(UseCase[ResetPasswordInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
        token_service: TokenService,
        password_hashing_service: PasswordHashingService,
    ):
        self._repository = repository
        self._token_service = token_service
        self._password_hashing_service = password_hashing_service

    def execute(self, input: ResetPasswordInput) -> UserOutput:
        user = self._repository.get_by_id(input.user_id)
        if user is None:
            raise UserNotFoundError(f"User with id {input.user_id} not found")

        if not self._token_service.verify_token(input.token, "password_reset"):
            raise InvalidTokenError("Invalid or expired token")

        new_password = Password(input.new_password)
        hashed_password = self._password_hashing_service.hash_password(new_password)

        user.update_password(hashed_password)
        user.add_domain_event(UserPasswordResetCompleted(user_id=user.id.value))

        saved_user = self._repository.save(user)

        return UserOutput(
            id=saved_user.id.value,
            email=saved_user.email.value,
            username=saved_user.username.value,
            is_active=saved_user.is_active,
            is_verified=saved_user.is_verified,
        )


class VerifyEmailUseCase(UseCase[VerifyEmailInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
        token_service: TokenService,
    ):
        self._repository = repository
        self._token_service = token_service

    def execute(self, input: VerifyEmailInput) -> UserOutput:
        user = self._repository.get_by_id(input.user_id)
        if user is None:
            raise UserNotFoundError(f"User with id {input.user_id} not found")

        if not self._token_service.verify_token(input.token, "email_verification"):
            raise InvalidTokenError("Invalid or expired token")

        user.verify_email()
        user.add_domain_event(UserEmailVerified(user_id=user.id.value))

        saved_user = self._repository.save(user)

        return UserOutput(
            id=saved_user.id.value,
            email=saved_user.email.value,
            username=saved_user.username.value,
            is_active=saved_user.is_active,
            is_verified=saved_user.is_verified,
        )


class GetUserUseCase(UseCase[int, UserOutput]):
    def __init__(self, repository: UserRepository):
        self._repository = repository

    def execute(self, user_id: int) -> UserOutput:
        user = self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with id {user_id} not found")

        return UserOutput(
            id=user.id.value,
            email=user.email.value,
            username=user.username.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
