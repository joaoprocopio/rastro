from http import HTTPStatus

import pytest
from django.test import Client

from rastro.iam.models import Identity
from rastro.iam.tests.factories import IdentityFactory
from rastro.iam.values import Email

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
