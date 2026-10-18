import pytest
from django.db import IntegrityError, connection, transaction

from rastro.common.values import InvalidValueError
from rastro.iam.models import Identity
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import DisplayName, Email


def test_the_table_is_iam_identity() -> None:
    assert Identity._meta.db_table == "iam_identity"


def test_created_at_replaces_date_joined() -> None:
    field_names = {field.name for field in Identity._meta.get_fields()}

    assert {"created_at", "updated_at"} <= field_names
    assert "date_joined" not in field_names


def test_required_fields_include_display_name() -> None:
    assert "display_name" in Identity.REQUIRED_FIELDS


@pytest.mark.django_db
def test_reading_an_identity_gives_value_objects() -> None:
    IdentityFactory.create(email=Email("ana@x.com"), display_name=DisplayName("Ana"))

    identity = Identity.objects.get()

    assert identity.email == Email("ana@x.com")
    assert identity.display_name == DisplayName("Ana")


@pytest.mark.django_db
def test_a_lookup_by_a_raw_email_finds_the_normalized_address() -> None:
    created = IdentityFactory.create(email=Email("ana@x.com"))

    found = Identity.objects.get(email=" Ana@X.com ")

    assert found.pk == created.pk


@pytest.mark.django_db
def test_the_database_refuses_an_email_with_uppercase_letters() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))

    with pytest.raises(IntegrityError), connection.cursor() as cursor:
        cursor.execute("UPDATE iam_identity SET email = 'Ana@x.com'")


@pytest.mark.django_db
def test_the_database_refuses_a_second_identity_with_the_same_email() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))

    with pytest.raises(IntegrityError), transaction.atomic():
        IdentityFactory.create(email=Email("ana@x.com"))


@pytest.mark.django_db
def test_an_invalid_email_from_the_database_raises() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))
    with connection.cursor() as cursor:
        cursor.execute("UPDATE iam_identity SET email = 'not-an-email'")

    with pytest.raises(InvalidValueError) as excinfo:
        Identity.objects.get()

    assert excinfo.value.code == "iam.invalid_email"


@pytest.mark.django_db
def test_str_is_the_email_address() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))

    assert str(Identity.objects.get()) == "ana@x.com"
