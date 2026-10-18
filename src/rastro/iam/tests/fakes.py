from django.http import HttpRequest

from rastro.iam.models import Identity
from rastro.iam.values import HashedPassword, RawPassword


class FakeSessionStore:
    def __init__(self) -> None:
        self.identity: Identity | None = None
        self.started: list[Identity] = []
        self.ended = 0

    def start(self, *, request: HttpRequest, identity: Identity) -> None:
        self.identity = identity
        self.started.append(identity)

    def end(self, *, request: HttpRequest) -> None:
        self.identity = None
        self.ended += 1

    def current(self, *, request: HttpRequest) -> Identity | None:
        return self.identity


def fake_hash(*, password: RawPassword) -> HashedPassword:
    return HashedPassword(f"fake${password.root}")
