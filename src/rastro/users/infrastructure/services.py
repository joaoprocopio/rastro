from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest

from rastro.base.entity import Id
from rastro.users.domain.aggregates import User
from rastro.users.domain.services import (
    EmailService,
    PasswordHashingService,
    SessionService,
    TokenService,
)
from rastro.users.domain.value_objects import HashedPassword, RawPassword


class DjangoPasswordHashingService(PasswordHashingService):
    def hash(self, password: RawPassword) -> HashedPassword:
        hashed = make_password(password.value)
        return HashedPassword(hashed)

    def verify(self, password: RawPassword, hashed: HashedPassword) -> bool:
        return check_password(password.value, hashed.value)


class DjangoSessionService(SessionService):
    def login(self, request: HttpRequest, user_id: Id) -> None:
        django_user = DjangoUser.objects.get(pk=user_id.value)  # type: ignore[misc]
        login(request, django_user)

    def logout(self, request: HttpRequest) -> None:
        logout(request)

    def get_current_user_id(self, request: HttpRequest) -> Id | None:
        pk = request.user.pk

        if pk is not None:
            return Id(int(pk))

        return None


class DjangoEmailService(EmailService):
    def send_verification_email(self, user: User, token: str) -> None:
        pass

    def send_password_reset_email(self, user: User, token: str) -> None:
        pass


class DjangoTokenService(TokenService):
    def generate_verification_token(self, user: User) -> str:
        django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]
        return default_token_generator.make_token(django_user)

    def generate_password_reset_token(self, user: User) -> str:
        django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]
        return default_token_generator.make_token(django_user)

    def verify_token(self, token: str, token_type: str) -> Id | None:
        return None
