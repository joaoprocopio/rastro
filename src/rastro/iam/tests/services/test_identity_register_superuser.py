import pytest

from rastro.iam.errors import EmailInUseError
from rastro.iam.models import Identity
from rastro.iam.ports import PasswordHasher
from rastro.iam.services import identity_register_superuser
from rastro.iam.values import DisplayName, Email, RawPassword


@pytest.mark.django_db
def test_it_creates_an_identity_with_the_staff_and_superuser_flags(
    password_hasher: PasswordHasher,
) -> None:
    identity_register_superuser(
        email=Email("root@x.com"),
        display_name=DisplayName("Root"),
        password=RawPassword("supersecret"),
        password_hasher=password_hasher,
    )

    identity = Identity.objects.get(email=Email("root@x.com"))
    assert identity.password == "fake$supersecret"
    assert identity.display_name == DisplayName("Root")
    assert identity.is_staff is True
    assert identity.is_superuser is True


def test_it_raises_email_in_use_for_an_email_that_an_identity_holds(
    identity: Identity, password_hasher: PasswordHasher
) -> None:
    with pytest.raises(EmailInUseError):
        identity_register_superuser(
            email=identity.email,
            display_name=DisplayName("Root"),
            password=RawPassword("supersecret"),
            password_hasher=password_hasher,
        )

    assert Identity.objects.get(email=identity.email).is_superuser is False
