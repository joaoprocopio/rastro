import pytest
from django.http import HttpRequest
from django.test import RequestFactory

from rastro.iam.errors import IncorrectCredentialsError
from rastro.iam.models import Identity
from rastro.iam.services import session_start
from rastro.iam.tests.fakes import FakeSessionStore
from rastro.iam.values import Email, RawPassword


def test_incorrect_credentials_raise_and_start_no_session(
    rf: RequestFactory, db: None, session_store: FakeSessionStore
) -> None:
    def refuse(
        *, request: HttpRequest, email: Email, password: RawPassword
    ) -> Identity | None:
        return None

    with pytest.raises(IncorrectCredentialsError):
        session_start(
            request=rf.post("/"),
            email=Email("nobody@example.com"),
            password=RawPassword("wrongpassword"),
            authenticator=refuse,
            session_store=session_store,
        )

    assert session_store.started == []


def test_correct_credentials_start_a_session_for_the_identity(
    rf: RequestFactory, identity: Identity, session_store: FakeSessionStore
) -> None:
    def accept(
        *, request: HttpRequest, email: Email, password: RawPassword
    ) -> Identity | None:
        return identity

    session_start(
        request=rf.post("/"),
        email=identity.email,
        password=RawPassword("password"),
        authenticator=accept,
        session_store=session_store,
    )

    assert session_store.started == [identity]
