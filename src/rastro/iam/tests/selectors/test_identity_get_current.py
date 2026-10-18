import pytest
from django.test import RequestFactory

from rastro.iam.errors import NotAuthenticatedError
from rastro.iam.models import Identity
from rastro.iam.selectors import identity_get_current
from rastro.iam.tests.fakes import FakeSessionStore


def test_returns_the_identity_of_the_current_session(
    rf: RequestFactory, identity: Identity, session_store: FakeSessionStore
) -> None:
    session_store.start(request=rf.post("/"), identity=identity)

    current = identity_get_current(request=rf.get("/"), session_store=session_store)

    assert current == identity


def test_raises_not_authenticated_without_a_session(
    rf: RequestFactory, db: None, session_store: FakeSessionStore
) -> None:
    with pytest.raises(NotAuthenticatedError):
        identity_get_current(request=rf.get("/"), session_store=session_store)
