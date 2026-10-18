from typing import Protocol

from django.http import HttpRequest

from rastro.iam.models import Identity
from rastro.iam.values import Email, HashedPassword, RawPassword


class Authenticator(Protocol):
    def __call__(
        self, *, request: HttpRequest, email: Email, password: RawPassword
    ) -> Identity | None: ...


class SessionStore(Protocol):
    def start(self, *, request: HttpRequest, identity: Identity) -> None: ...

    def end(self, *, request: HttpRequest) -> None: ...

    def current(self, *, request: HttpRequest) -> Identity | None: ...


class PasswordHasher(Protocol):
    def __call__(self, *, password: RawPassword) -> HashedPassword: ...
