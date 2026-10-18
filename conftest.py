import pytest

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
