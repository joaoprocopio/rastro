import pytest
from django.http import HttpRequest
from django.test import RequestFactory

from rastro.iam.errors import IncorrectCredentialsError
from rastro.iam.models import Identity
from rastro.iam.services import session_start
from rastro.iam.tests.fakes import FakeSessionStore
from rastro.iam.values import Email, RawPassword


def _refuse(
    *, request: HttpRequest, email: Email, password: RawPassword
) -> Identity | None:
    return None


def test_incorrect_credentials_raise_and_start_no_session(
    rf: RequestFactory, db: None
) -> None:
    session_store = FakeSessionStore()

    with pytest.raises(IncorrectCredentialsError):
        session_start(
            request=rf.post("/"),
            email=Email("nobody@example.com"),
            password=RawPassword("wrongpassword"),
            authenticator=_refuse,
            session_store=session_store,
        )

    assert session_store.started == []


def test_correct_credentials_start_a_session_for_the_identity(
    rf: RequestFactory, db: None
) -> None:
    identity = Identity(email=Email("ada@example.com"))
    session_store = FakeSessionStore()

    def accept(
        *, request: HttpRequest, email: Email, password: RawPassword
    ) -> Identity | None:
        return identity

    session_start(
        request=rf.post("/"),
        email=Email("ada@example.com"),
        password=RawPassword("supersecret"),
        authenticator=accept,
        session_store=session_store,
    )

    assert session_store.started == [identity]
