from django.http import HttpRequest
from django.test import RequestFactory

from rastro.iam.models import Identity
from rastro.iam.services import session_end


class FakeSessionStore:
    def __init__(self, identity: Identity | None) -> None:
        self.identity = identity
        self.ended = 0

    def start(self, *, request: HttpRequest, identity: Identity) -> None:
        self.identity = identity

    def end(self, *, request: HttpRequest) -> None:
        self.identity = None
        self.ended += 1

    def current(self, *, request: HttpRequest) -> Identity | None:
        return self.identity


def test_ends_the_current_session(rf: RequestFactory, identity: Identity) -> None:
    session_store = FakeSessionStore(identity)

    session_end(request=rf.post("/"), session_store=session_store)

    assert session_store.current(request=rf.get("/")) is None


def test_succeeds_without_a_session(rf: RequestFactory, db: None) -> None:
    session_store = FakeSessionStore(None)

    session_end(request=rf.post("/"), session_store=session_store)

    assert session_store.ended == 1
