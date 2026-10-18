from http import HTTPStatus

import pytest
from django.test import Client

from rastro.iam.models import Identity
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import DisplayName, Email

ADD_IDENTITY_URL = "/admin/iam/identity/add/"


@pytest.fixture
def admin_client(db: None) -> Client:
    administrator = IdentityFactory.create(is_staff=True, is_superuser=True)
    client = Client()
    client.force_login(administrator)
    return client


def test_the_admin_rejects_an_invalid_email_on_the_email_field(
    admin_client: Client,
) -> None:
    response = admin_client.post(
        ADD_IDENTITY_URL,
        {"email": "not-an-email", "display_name": "Ana", "password": "supersecret"},
    )

    assert response.status_code == HTTPStatus.OK
    [error] = response.context["adminform"].form.errors.as_data()["email"]
    assert error.code == "iam.invalid_email"
    assert not Identity.objects.filter(display_name="Ana").exists()


def test_the_admin_stores_a_normalized_email(admin_client: Client) -> None:
    response = admin_client.post(
        ADD_IDENTITY_URL,
        {"email": " Ana@X.com ", "display_name": "Ana", "password": "supersecret"},
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Identity.objects.get(display_name="Ana").email == Email("ana@x.com")


def test_the_admin_stores_a_hashed_password(admin_client: Client) -> None:
    admin_client.post(
        ADD_IDENTITY_URL,
        {"email": "ana@x.com", "display_name": "Ana", "password": "supersecret"},
    )

    identity = Identity.objects.get(email=Email("ana@x.com"))
    assert identity.password != "supersecret"
    assert identity.check_password("supersecret")


def test_the_admin_rejects_a_short_password_on_the_password_field(
    admin_client: Client,
) -> None:
    response = admin_client.post(
        ADD_IDENTITY_URL,
        {"email": "ana@x.com", "display_name": "Ana", "password": "short"},
    )

    assert response.status_code == HTTPStatus.OK
    [error] = response.context["adminform"].form.errors.as_data()["password"]
    assert error.code == "iam.invalid_password"
    assert not Identity.objects.filter(display_name="Ana").exists()


def test_the_change_page_shows_the_hash_without_a_password_input(
    admin_client: Client,
) -> None:
    identity = IdentityFactory.create(email=Email("ana@x.com"))

    response = admin_client.get(f"/admin/iam/identity/{identity.pk}/change/")

    assert response.status_code == HTTPStatus.OK
    assert 'name="password"' not in response.content.decode()
    assert response.context["adminform"].form.fields["password"].disabled


def test_the_change_page_shows_the_email_as_typed_text(admin_client: Client) -> None:
    identity = IdentityFactory.create(email=Email("ana@x.com"))

    response = admin_client.get(f"/admin/iam/identity/{identity.pk}/change/")

    assert 'value="ana@x.com"' in response.content.decode()


def test_the_change_page_edits_the_flags_and_keeps_the_hash(
    admin_client: Client,
) -> None:
    identity = IdentityFactory.create(
        email=Email("ana@x.com"), display_name=DisplayName("Ana")
    )
    password_hash = identity.password

    response = admin_client.post(
        f"/admin/iam/identity/{identity.pk}/change/",
        {
            "email": "ana@x.com",
            "display_name": "Ana",
            "password": "plain-text-attempt",
            "is_staff": "on",
            "is_superuser": "on",
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    identity.refresh_from_db()
    assert identity.is_active is False
    assert identity.is_staff is True
    assert identity.is_superuser is True
    assert identity.password == password_hash
