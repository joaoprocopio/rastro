import pytest

from rastro.iam.errors import EmailInUseError
from rastro.iam.models import Identity
from rastro.iam.services import identity_register
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import DisplayName, Email, HashedPassword, RawPassword


def fake_hash(*, password: RawPassword) -> HashedPassword:
    return HashedPassword(f"fake${password.value}")


@pytest.mark.django_db
def test_it_stores_the_hash_that_the_hasher_returns() -> None:
    identity_register(
        email=Email("ana@x.com"),
        display_name=DisplayName("Ana"),
        password=RawPassword("supersecret"),
        password_hasher=fake_hash,
    )

    identity = Identity.objects.get(email=Email("ana@x.com"))
    assert identity.password == "fake$supersecret"
    assert identity.display_name == DisplayName("Ana")
    assert identity.is_staff is False
    assert identity.is_superuser is False
