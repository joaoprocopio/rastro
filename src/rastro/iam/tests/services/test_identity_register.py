import pytest

from rastro.iam.errors import EmailInUseError
from rastro.iam.models import Identity
from rastro.iam.ports import PasswordHasher
from rastro.iam.services import identity_register
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import DisplayName, Email, HashedPassword, RawPassword


@pytest.mark.django_db
def test_it_stores_the_hash_that_the_hasher_returns(
    password_hasher: PasswordHasher,
) -> None:
    identity_register(
        email=Email("ana@x.com"),
        display_name=DisplayName("Ana"),
        password=RawPassword("supersecret"),
        password_hasher=password_hasher,
    )

    identity = Identity.objects.get(email=Email("ana@x.com"))
    assert identity.password == "fake$supersecret"
    assert identity.display_name == DisplayName("Ana")
    assert identity.is_staff is False
    assert identity.is_superuser is False


def test_it_raises_email_in_use_for_an_email_that_an_identity_holds(
    identity: Identity, password_hasher: PasswordHasher
) -> None:
    with pytest.raises(EmailInUseError):
        identity_register(
            email=identity.email,
            display_name=DisplayName("Ana"),
            password=RawPassword("supersecret"),
            password_hasher=password_hasher,
        )

    assert Identity.objects.filter(email=identity.email).count() == 1


@pytest.mark.django_db
def test_it_raises_email_in_use_when_a_concurrent_registration_wins(
    password_hasher: PasswordHasher,
) -> None:
    def hash_while_another_registration_lands(
        *, password: RawPassword
    ) -> HashedPassword:
        # A second request inserts the same email between the check and the insert.
        IdentityFactory.create(email=Email("ana@x.com"))
        return password_hasher(password=password)

    with pytest.raises(EmailInUseError):
        identity_register(
            email=Email("ana@x.com"),
            display_name=DisplayName("Ana"),
            password=RawPassword("supersecret"),
            password_hasher=hash_while_another_registration_lands,
        )
