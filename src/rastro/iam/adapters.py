from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.http import HttpRequest

from rastro.iam.models import Identity
from rastro.iam.ports import Authenticator, PasswordHasher, SessionStore
from rastro.iam.values import Email, HashedPassword, RawPassword


def django_authenticate(
    *, request: HttpRequest, email: Email, password: RawPassword
) -> Identity | None:
    user = auth.authenticate(request, email=email, password=password.value)
    return user if isinstance(user, Identity) else None


_authenticator: Authenticator = django_authenticate


class DjangoSessionStore:
    def start(self, *, request: HttpRequest, identity: Identity) -> None:
        auth.login(request, identity)

    def end(self, *, request: HttpRequest) -> None:
        auth.logout(request)

    def current(self, *, request: HttpRequest) -> Identity | None:
        user = auth.get_user(request)
        return user if isinstance(user, Identity) else None


_session_store: SessionStore = DjangoSessionStore()


def django_make_password(*, password: RawPassword) -> HashedPassword:
    return HashedPassword(make_password(password.value))


_password_hasher: PasswordHasher = django_make_password
