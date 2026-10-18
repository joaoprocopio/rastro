import pytest
from django.contrib.auth.models import AnonymousUser

from rastro.iam.models import Identity
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import DisplayName, Email


@pytest.fixture
def identity(db: None) -> Identity:
    return IdentityFactory.create(
        email=Email("user@example.com"),
        display_name=DisplayName("user"),
        password="password",
    )


@pytest.fixture
def anonymous_user(db: None) -> AnonymousUser:
    return AnonymousUser()
