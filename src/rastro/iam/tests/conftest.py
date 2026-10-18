import pytest
from django.test import Client

from rastro.iam.models import Identity
from rastro.iam.ports import PasswordHasher
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.tests.fakes import FakeSessionStore, fake_hash
from rastro.iam.values import DisplayName, Email


@pytest.fixture
def identity(db: None) -> Identity:
    return IdentityFactory.create(
        email=Email("ana@example.com"),
        display_name=DisplayName("Ana"),
        password="password",
    )


@pytest.fixture
def signed_in_client(identity: Identity) -> Client:
    client = Client()
    client.force_login(identity)
    return client


@pytest.fixture
def admin_client(db: None) -> Client:
    administrator = IdentityFactory.create(is_staff=True, is_superuser=True)
    client = Client()
    client.force_login(administrator)
    return client


@pytest.fixture
def session_store() -> FakeSessionStore:
    return FakeSessionStore()


@pytest.fixture
def password_hasher() -> PasswordHasher:
    return fake_hash
