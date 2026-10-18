import pytest

from rastro.iam.errors import EmailInUseError
from rastro.iam.models import Identity
from rastro.iam.services import identity_register_superuser
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import DisplayName, Email, HashedPassword, RawPassword


def fake_hash(*, password: RawPassword) -> HashedPassword:
    return HashedPassword(f"fake${password.value}")


@pytest.mark.django_db
def test_it_creates_an_identity_with_the_staff_and_superuser_flags() -> None:
    identity_register_superuser(
        email=Email("root@x.com"),
        display_name=DisplayName("Root"),
        password=RawPassword("supersecret"),
        password_hasher=fake_hash,
    )

    identity = Identity.objects.get(email=Email("root@x.com"))
    assert identity.password == "fake$supersecret"
    assert identity.display_name == DisplayName("Root")
    assert identity.is_staff is True
    assert identity.is_superuser is True


@pytest.mark.django_db
def test_it_raises_email_in_use_for_an_email_that_an_identity_holds() -> None:
    IdentityFactory.create(email=Email("root@x.com"))

    with pytest.raises(EmailInUseError):
        identity_register_superuser(
            email=Email("root@x.com"),
            display_name=DisplayName("Root"),
            password=RawPassword("supersecret"),
            password_hasher=fake_hash,
        )

    assert Identity.objects.get(email=Email("root@x.com")).is_superuser is False
