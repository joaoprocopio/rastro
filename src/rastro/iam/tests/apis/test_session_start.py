import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.hashers import MD5PasswordHasher, make_password
from django.test import Client, override_settings

from rastro.iam.models import Identity

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

SESSION_START_URL = "/api/v1/iam/session/start"


class RecordingHasher(MD5PasswordHasher):
    algorithm = "recording"
    encoded: list[str] = []

    def encode(self, password: str, salt: str) -> str:
        self.encoded.append(password)
        return super().encode(password, salt)


def _start_session(
    client: Client, payload: dict[str, str]
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(
        SESSION_START_URL, data=json.dumps(payload), content_type="application/json"
    )


def test_correct_credentials_start_a_session(
    client: Client, identity: Identity
) -> None:
    response = _start_session(
        client, {"email": identity.email.value, "password": "password"}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert settings.SESSION_COOKIE_NAME in response.cookies


def test_a_wrong_password_and_an_unknown_email_answer_the_same_problem(
    client: Client, identity: Identity
) -> None:
    wrong_password = _start_session(
        client, {"email": identity.email.value, "password": "wrongpassword"}
    )
    unknown_email = _start_session(
        client, {"email": "nobody@example.com", "password": "wrongpassword"}
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

    response = _start_session(
        client, {"email": identity.email.value, "password": "password"}
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

    response = _start_session(
        client, {"email": "nobody@example.com", "password": "wrongpassword"}
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

    response = _start_session(
        client, {"email": identity.email.value, "password": "password"}
    )

    identity.refresh_from_db()
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert identity.password.startswith("md5$")
    assert identity.check_password("password")


def test_a_session_start_records_last_login(
    client: Client, identity: Identity
) -> None:
    assert identity.last_login is None

    _start_session(client, {"email": identity.email.value, "password": "password"})

    identity.refresh_from_db()
    assert identity.last_login is not None


def test_a_session_start_while_a_session_exists_succeeds(
    client: Client, identity: Identity
) -> None:
    payload = {"email": identity.email.value, "password": "password"}
    first = _start_session(client, payload)

    second = _start_session(client, payload)

    assert first.status_code == HTTPStatus.NO_CONTENT
    assert second.status_code == HTTPStatus.NO_CONTENT
    assert settings.SESSION_COOKIE_NAME in second.cookies
