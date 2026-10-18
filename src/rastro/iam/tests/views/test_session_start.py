from http import HTTPStatus

from django.conf import settings
from django.contrib.auth.hashers import MD5PasswordHasher, make_password
from django.test import Client, override_settings
from django.urls import reverse

from rastro.iam.models import Identity


class RecordingHasher(MD5PasswordHasher):
    algorithm = "recording"
    encoded: list[str] = []

    def encode(self, password: str, salt: str) -> str:
        self.encoded.append(password)
        return super().encode(password, salt)


def test_correct_credentials_start_a_session(
    client: Client, identity: Identity
) -> None:
    response = client.post(
        reverse("iam:session_start"),
        {"email": identity.email.root, "password": "password"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert settings.SESSION_COOKIE_NAME in response.cookies


def test_a_wrong_password_and_an_unknown_email_answer_the_same_problem(
    client: Client, identity: Identity
) -> None:
    wrong_password = client.post(
        reverse("iam:session_start"),
        {"email": identity.email.root, "password": "wrongpassword"},
        content_type="application/json",
    )
    unknown_email = client.post(
        reverse("iam:session_start"),
        {"email": "nobody@example.com", "password": "wrongpassword"},
        content_type="application/json",
    )

    assert wrong_password.status_code == HTTPStatus.UNAUTHORIZED
    assert wrong_password["Content-Type"] == "application/problem+json"
    assert wrong_password.json() == {
        "type": "/problems/iam.incorrect_credentials",
        "status": 401,
    }
    assert unknown_email.status_code == HTTPStatus.UNAUTHORIZED
    assert unknown_email["Content-Type"] == wrong_password["Content-Type"]
    assert unknown_email.json() == wrong_password.json()
    assert settings.SESSION_COOKIE_NAME not in wrong_password.cookies
    assert settings.SESSION_COOKIE_NAME not in unknown_email.cookies


def test_an_inactive_identity_answers_the_same_problem(
    client: Client, identity: Identity
) -> None:
    identity.is_active = False
    identity.save(update_fields=["is_active"])

    response = client.post(
        reverse("iam:session_start"),
        {"email": identity.email.root, "password": "password"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        "type": "/problems/iam.incorrect_credentials",
        "status": 401,
    }
    assert settings.SESSION_COOKIE_NAME not in response.cookies


@override_settings(
    PASSWORD_HASHERS=[
        f"{RecordingHasher.__module__}.{RecordingHasher.__qualname__}",
        *settings.PASSWORD_HASHERS,
    ]
)
def test_an_unknown_email_runs_the_password_hasher(client: Client, db: None) -> None:
    RecordingHasher.encoded.clear()

    response = client.post(
        reverse("iam:session_start"),
        {"email": "nobody@example.com", "password": "wrongpassword"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert RecordingHasher.encoded == ["wrongpassword"]


@override_settings(
    PASSWORD_HASHERS=[
        *settings.PASSWORD_HASHERS,
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
def test_a_session_start_upgrades_an_outdated_hash(
    client: Client, identity: Identity
) -> None:
    identity.password = make_password("password", hasher="pbkdf2_sha256")
    identity.save(update_fields=["password"])

    response = client.post(
        reverse("iam:session_start"),
        {"email": identity.email.root, "password": "password"},
        content_type="application/json",
    )

    identity.refresh_from_db()
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert identity.password.startswith("md5$")
    assert identity.check_password("password")


def test_a_session_start_records_last_login(client: Client, identity: Identity) -> None:
    assert identity.last_login is None

    client.post(
        reverse("iam:session_start"),
        {"email": identity.email.root, "password": "password"},
        content_type="application/json",
    )

    identity.refresh_from_db()
    assert identity.last_login is not None


def test_a_session_start_while_a_session_exists_succeeds(
    client: Client, identity: Identity
) -> None:
    credentials = {"email": identity.email.root, "password": "password"}
    first = client.post(
        reverse("iam:session_start"), credentials, content_type="application/json"
    )

    second = client.post(
        reverse("iam:session_start"), credentials, content_type="application/json"
    )

    assert first.status_code == HTTPStatus.NO_CONTENT
    assert second.status_code == HTTPStatus.NO_CONTENT
    assert settings.SESSION_COOKIE_NAME in second.cookies
