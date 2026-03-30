from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User as DjangoUser
from django.http import HttpRequest

from rastro.users.domain.aggregates import User
from rastro.users.domain.services import (
    AuthenticationService,
    EmailService,
    PasswordHashingService,
    TokenService,
)
from rastro.users.domain.value_objects import HashedPassword, Password


class DjangoPasswordHashingService(PasswordHashingService):
    def hash_password(self, password: Password) -> HashedPassword:
        hashed = make_password(password.value)
        return HashedPassword(hashed)

    def verify_password(
        self, password: Password, hashed_password: HashedPassword
    ) -> bool:
        return check_password(password.value, hashed_password.value)


class DjangoAuthenticationService(AuthenticationService):
    def __init__(self, password_hashing_service: PasswordHashingService):
        self._password_hashing_service = password_hashing_service

    def authenticate(self, user: User, password: Password) -> bool:
        django_user = DjangoUser.objects.get(pk=user.id.value)
        return self._password_hashing_service.verify_password(
            password, HashedPassword(django_user.password)
        )

    def login(self, request: HttpRequest, user: User) -> None:
        django_user = DjangoUser.objects.get(pk=user.id.value)
        login(request, django_user)

    def logout(self, request: HttpRequest) -> None:
        logout(request)


class DjangoSessionAuthenticationService(AuthenticationService):
    def __init__(self, password_hashing_service: PasswordHashingService):
        self._password_hashing_service = password_hashing_service

    def authenticate(self, user: User, password: Password) -> bool:
        if user.id is None:
            return False
        try:
            django_user = DjangoUser.objects.get(pk=user.id.value)
            return self._password_hashing_service.verify_password(
                password, HashedPassword(django_user.password)
            )
        except DjangoUser.DoesNotExist:
            return False

    def login(self, user: User) -> str:
        raise NotImplementedError("Use DjangoAuthenticationService.login with request")

    def logout(self, user: User) -> None:
        raise NotImplementedError("Use DjangoAuthenticationService.logout with request")


class DjangoEmailService(EmailService):
    def send_verification_email(self, user: User, token: str) -> None:
        pass

    def send_password_reset_email(self, user: User, token: str) -> None:
        pass


class DjangoTokenService(TokenService):
    def generate_verification_token(self, user: User) -> str:
        from django.contrib.auth.tokens import default_token_generator

        django_user = DjangoUser.objects.get(pk=user.id.value)
        return default_token_generator.make_token(django_user)

    def generate_password_reset_token(self, user: User) -> str:
        from django.contrib.auth.tokens import default_token_generator

        django_user = DjangoUser.objects.get(pk=user.id.value)
        return default_token_generator.make_token(django_user)

    def verify_token(self, token: str, token_type: str) -> int | None:
        return None
