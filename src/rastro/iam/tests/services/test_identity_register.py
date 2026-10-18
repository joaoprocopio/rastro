import pytest

from rastro.iam.errors import EmailInUseError
from rastro.iam.models import Identity
from rastro.iam.services import identity_register
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.tests.fakes import fake_hash
from rastro.iam.values import DisplayName, Email, HashedPassword, RawPassword


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


@pytest.mark.django_db
def test_it_raises_email_in_use_for_an_email_that_an_identity_holds() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))

    with pytest.raises(EmailInUseError):
        identity_register(
            email=Email("ana@x.com"),
            display_name=DisplayName("Ana"),
            password=RawPassword("supersecret"),
            password_hasher=fake_hash,
        )

    assert Identity.objects.filter(email=Email("ana@x.com")).count() == 1


@pytest.mark.django_db
def test_it_raises_email_in_use_when_a_concurrent_registration_wins() -> None:
    def hash_while_another_registration_lands(
        *, password: RawPassword
    ) -> HashedPassword:
        # A second request inserts the same email between the check and the insert.
        IdentityFactory.create(email=Email("ana@x.com"))
        return fake_hash(password=password)

    with pytest.raises(EmailInUseError):
        identity_register(
            email=Email("ana@x.com"),
            display_name=DisplayName("Ana"),
            password=RawPassword("supersecret"),
            password_hasher=hash_while_another_registration_lands,
        )
