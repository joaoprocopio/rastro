import pydantic
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction

from rastro.iam.errors import EmailInUseError
from rastro.iam.models import Identity, IdentityManager
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

    with pytest.raises(pydantic.ValidationError):
        Identity.objects.get()


@pytest.mark.django_db
def test_str_is_the_email_address() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))

    assert str(Identity.objects.get()) == "ana@x.com"


def test_the_manager_holds_only_create_user_and_create_superuser() -> None:
    public_names = {name for name in vars(IdentityManager) if not name.startswith("_")}

    assert public_names == {"create_user", "create_superuser"}
    assert IdentityManager.use_in_migrations is False
    assert not hasattr(IdentityManager.create_user, "alters_data")
    assert not hasattr(IdentityManager.create_superuser, "alters_data")


@pytest.mark.django_db
def test_create_user_parses_raw_strings_and_returns_the_identity() -> None:
    identity = Identity.objects.create_user(
        email=" Ana@X.com ", display_name=" Ana ", password="supersecret"
    )

    assert identity.pk is not None
    assert identity.email == Email("ana@x.com")
    assert identity.display_name == DisplayName("Ana")
    assert identity.check_password("supersecret")
    assert identity.is_staff is False
    assert identity.is_superuser is False


@pytest.mark.django_db
def test_create_superuser_accepts_value_objects_and_sets_the_flags() -> None:
    identity = Identity.objects.create_superuser(
        email=Email("root@x.com"),
        display_name=DisplayName("Root"),
        password="supersecret",
    )

    assert identity.email == Email("root@x.com")
    assert identity.check_password("supersecret")
    assert identity.is_staff is True
    assert identity.is_superuser is True


@pytest.mark.django_db
def test_create_user_rejects_an_invalid_email_with_a_validation_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Identity.objects.create_user(
            email="not-an-email", display_name="Ana", password="supersecret"
        )

    assert [error.code for error in excinfo.value.error_list] == [
        "request.invalid_format"
    ]
    assert not Identity.objects.exists()


@pytest.mark.django_db
def test_create_user_rejects_a_short_password_with_a_validation_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Identity.objects.create_user(
            email="ana@x.com", display_name="Ana", password="short"
        )

    assert [error.code for error in excinfo.value.error_list] == ["request.too_short"]
    assert not Identity.objects.exists()


@pytest.mark.django_db
def test_create_user_rejects_a_missing_password_with_a_validation_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Identity.objects.create_user(
            email="ana@x.com", display_name="Ana", password=None
        )

    assert [error.code for error in excinfo.value.error_list] == ["request.too_short"]


@pytest.mark.django_db
def test_create_user_raises_email_in_use_for_an_email_that_an_identity_holds() -> None:
    IdentityFactory.create(email=Email("ana@x.com"))

    with pytest.raises(EmailInUseError):
        Identity.objects.create_user(
            email="ana@x.com", display_name="Ana", password="supersecret"
        )
