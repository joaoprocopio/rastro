from datetime import timedelta
from http import HTTPStatus

import httpx2
import sqlalchemy as sa
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from rastro.config import get_settings
from rastro.iam.models import Identity
from rastro.iam.session.models import IdentitySession
from rastro.problem import PROBLEM_MEDIA_TYPE
from rastro.security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SESSION_COOKIE_NAME

IDENTITIES_URL = "/api/v1/iam/identities"
SESSION_URL = "/api/v1/iam/session"
CSRFTOKEN_URL = "/api/v1/iam/csrftoken"

PASSWORD = "password"  # the `identity` fixture's password
REGISTRATION = {
    "display_name": "Ada",
    "email": "ada@example.com",
    "password": "supersecret",
}


def _csrf(client: TestClient) -> dict[str, str]:
    return {CSRF_HEADER_NAME: client.cookies[CSRF_COOKIE_NAME]}


def _post(client: TestClient, url: str, payload: dict[str, str]) -> httpx2.Response:
    return client.post(url, json=payload, headers=_csrf(client))


def _sign_in(client: TestClient, identity: Identity) -> httpx2.Response:
    return _post(client, SESSION_URL, {"email": identity.email, "password": PASSWORD})


def _set_cookie_header(response: httpx2.Response, name: str) -> str:
    headers = response.headers.get_list("set-cookie")
    return next(header for header in headers if header.startswith(f"{name}="))


def test_register_returns_public_identity(client: TestClient) -> None:
    response = _post(client, IDENTITIES_URL, REGISTRATION)

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {"display_name": "Ada", "email": "ada@example.com"}


def test_register_signs_the_identity_in(client: TestClient) -> None:
    _post(client, IDENTITIES_URL, REGISTRATION)

    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"display_name": "Ada", "email": "ada@example.com"}


def test_register_normalizes_the_email(client: TestClient) -> None:
    response = _post(
        client, IDENTITIES_URL, {**REGISTRATION, "email": "  Ada@Example.COM "}
    )

    assert response.json()["email"] == "ada@example.com"


def test_register_stores_an_argon2id_hash(
    client: TestClient, db_session: Session
) -> None:
    _post(client, IDENTITIES_URL, REGISTRATION)

    password_hash = db_session.scalars(sa.select(Identity.password_hash)).one()

    assert password_hash.startswith("$argon2id$")
    assert REGISTRATION["password"] not in password_hash


def test_register_with_a_taken_email_conflicts(
    client: TestClient, identity: Identity
) -> None:
    response = _post(client, IDENTITIES_URL, {**REGISTRATION, "email": identity.email})

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    assert response.json()["code"] == "IAM_EMAIL_ALREADY_REGISTERED"


def test_register_rejects_a_short_password_without_echoing_it(
    client: TestClient,
) -> None:
    response = _post(client, IDENTITIES_URL, {**REGISTRATION, "password": "s3cr3t!"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "BASE_VALIDATION_ERROR"
    assert "s3cr3t!" not in response.text


def test_register_keeps_the_whitespace_of_the_password(client: TestClient) -> None:
    _post(client, IDENTITIES_URL, {**REGISTRATION, "password": " supersecret "})
    credentials = {"email": REGISTRATION["email"], "password": "supersecret"}

    stripped = _post(client, SESSION_URL, credentials)
    exact = _post(client, SESSION_URL, {**credentials, "password": " supersecret "})

    assert stripped.status_code == HTTPStatus.UNAUTHORIZED
    assert exact.status_code == HTTPStatus.OK


def test_register_rejects_unknown_fields(client: TestClient) -> None:
    response = _post(client, IDENTITIES_URL, {**REGISTRATION, "is_active": "false"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_session_cookie_is_hardened(client: TestClient) -> None:
    response = _post(client, IDENTITIES_URL, REGISTRATION)

    cookie = _set_cookie_header(response, SESSION_COOKIE_NAME).lower()

    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "max-age" not in cookie


def test_authenticate_success(client: TestClient, identity: Identity) -> None:
    response = _sign_in(client, identity)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "display_name": identity.display_name,
        "email": identity.email,
    }


def test_authenticate_records_the_last_login(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    _sign_in(client, identity)

    db_session.refresh(identity)
    assert identity.last_login is not None


def test_authenticate_failures_are_indistinguishable(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    wrong_password = _post(
        client, SESSION_URL, {"email": identity.email, "password": "wrongpassword"}
    )
    unknown_email = _post(
        client,
        SESSION_URL,
        {"email": "nobody@example.com", "password": "wrongpassword"},
    )
    identity.is_active = False
    db_session.commit()
    inactive = _sign_in(client, identity)

    for response in (wrong_password, unknown_email, inactive):
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    assert wrong_password.json() == unknown_email.json() == inactive.json()


def test_authenticate_upgrades_an_outdated_hash(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    outdated_hasher = PasswordHasher(time_cost=1, memory_cost=8 * 1024, parallelism=1)
    identity.password_hash = outdated_hasher.hash(PASSWORD)
    db_session.commit()

    _sign_in(client, identity)

    db_session.refresh(identity)
    assert not identity.password_hash.startswith("$argon2id$v=19$m=8192,t=1,p=1$")
    assert identity.password_hash.startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_authenticate_replaces_the_previous_session(
    client: TestClient, identity: Identity
) -> None:
    _sign_in(client, identity)
    first_token = client.cookies[SESSION_COOKIE_NAME]

    _sign_in(client, identity)
    second_token = client.cookies[SESSION_COOKIE_NAME]

    assert first_token != second_token
    client.cookies.set(SESSION_COOKIE_NAME, first_token)
    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_the_database_stores_a_digest_of_the_session_token(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    _sign_in(client, identity)
    token = client.cookies[SESSION_COOKIE_NAME]

    digests = db_session.scalars(sa.select(IdentitySession.token_digest)).all()

    assert len(digests) == 1
    assert token.encode() not in digests


def test_current_identity_when_unauthenticated(client: TestClient) -> None:
    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["code"] == "IAM_NOT_AUTHENTICATED"


def test_current_identity_with_a_forged_token(client: TestClient) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, "forged")

    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_session_expires_after_the_idle_timeout(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    _sign_in(client, identity)
    idle_timeout = get_settings().session_idle_timeout
    db_session.execute(
        sa.update(IdentitySession).values(
            last_seen_at=IdentitySession.last_seen_at - idle_timeout
        )
    )
    db_session.commit()

    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_session_expires_at_the_absolute_timeout(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    _sign_in(client, identity)
    db_session.execute(
        sa.update(IdentitySession).values(
            expires_at=sa.func.now() - timedelta(seconds=1)
        )
    )
    db_session.commit()

    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_session_of_a_deactivated_identity_stops_working(
    client: TestClient, identity: Identity, db_session: Session
) -> None:
    _sign_in(client, identity)
    identity.is_active = False
    db_session.commit()

    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_end_session(client: TestClient, identity: Identity) -> None:
    _sign_in(client, identity)
    token = client.cookies[SESSION_COOKIE_NAME]

    response = client.delete(SESSION_URL, headers=_csrf(client))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert SESSION_COOKIE_NAME not in client.cookies
    # the server forgot the session, so replaying the old cookie fails too
    client.cookies.set(SESSION_COOKIE_NAME, token)
    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_end_session_without_a_session(client: TestClient) -> None:
    response = client.delete(SESSION_URL, headers=_csrf(client))

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_csrftoken_issues_a_readable_cookie(client: TestClient) -> None:
    response = client.get(CSRFTOKEN_URL)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert "httponly" not in _set_cookie_header(response, CSRF_COOKIE_NAME).lower()


def test_unsafe_request_without_csrf_header_is_forbidden(client: TestClient) -> None:
    response = client.post(IDENTITIES_URL, json=REGISTRATION)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["code"] == "BASE_CSRF_FAILED"


def test_unsafe_request_with_a_forged_csrf_token_is_forbidden(
    client: TestClient,
) -> None:
    client.cookies.set(CSRF_COOKIE_NAME, "forged.token")

    response = client.post(
        IDENTITIES_URL, json=REGISTRATION, headers={CSRF_HEADER_NAME: "forged.token"}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_unsafe_request_from_a_foreign_origin_is_forbidden(
    client: TestClient,
) -> None:
    response = client.post(
        IDENTITIES_URL,
        json=REGISTRATION,
        headers={**_csrf(client), "Origin": "https://evil.example"},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_unsafe_request_from_a_trusted_origin_is_allowed(
    client: TestClient,
) -> None:
    response = client.post(
        IDENTITIES_URL,
        json=REGISTRATION,
        headers={**_csrf(client), "Origin": "https://trusted.example"},
    )

    assert response.status_code == HTTPStatus.CREATED


def test_csrf_token_rotates_with_the_session(
    client: TestClient, identity: Identity
) -> None:
    anonymous_headers = _csrf(client)
    _sign_in(client, identity)

    response = client.delete(SESSION_URL, headers=anonymous_headers)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_malformed_json_is_unprocessable(client: TestClient) -> None:
    response = client.post(
        IDENTITIES_URL,
        content=b"{not valid",
        headers={**_csrf(client), "Content-Type": "application/json"},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
