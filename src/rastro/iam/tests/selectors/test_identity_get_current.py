import pytest
from django.http import HttpRequest
from django.test import RequestFactory

from rastro.iam.errors import NotAuthenticatedError
from rastro.iam.models import Identity
from rastro.iam.selectors import identity_get_current


class FakeSessionStore:
    def __init__(self, identity: Identity | None) -> None:
        self.identity = identity

    def start(self, *, request: HttpRequest, identity: Identity) -> None:
        self.identity = identity

    def end(self, *, request: HttpRequest) -> None:
        self.identity = None

    def current(self, *, request: HttpRequest) -> Identity | None:
        return self.identity


def test_returns_the_identity_of_the_current_session(
    rf: RequestFactory, identity: Identity
) -> None:
    current = identity_get_current(
        request=rf.get("/"), session_store=FakeSessionStore(identity)
    )

    assert current == identity


def test_raises_not_authenticated_without_a_session(
    rf: RequestFactory, db: None
) -> None:
    with pytest.raises(NotAuthenticatedError):
        identity_get_current(request=rf.get("/"), session_store=FakeSessionStore(None))
