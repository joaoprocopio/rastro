from http import HTTPStatus

import httpx
from procrastinate import App

from rastro.auth.domain.aggregates import User
from rastro.auth.tests.fakes import FakeEmailSender

REQUEST_PATH = "/api/v1/auth/password-reset/request"
CONFIRM_PATH = "/api/v1/auth/password-reset/confirm"
SESSION_START_PATH = "/api/v1/auth/session/start"
NEW_PASSWORD = "newpassword"


async def test_a_user_who_asks_for_a_reset_starts_a_session_with_the_new_password(
    client: httpx.AsyncClient,
    worker_app: App,
    email_sender: FakeEmailSender,
    user: User,
) -> None:
    requested = await client.post(REQUEST_PATH, json={"email": user.email.root})
    await worker_app.run_worker_async()
    token = email_sender.last_reset_token().root.get_secret_value()

    confirmed = await client.post(
        CONFIRM_PATH, json={"token": token, "password": NEW_PASSWORD}
    )

    assert requested.status_code == HTTPStatus.NO_CONTENT
    assert confirmed.status_code == HTTPStatus.NO_CONTENT
    new = await client.post(
        SESSION_START_PATH, json={"email": user.email.root, "password": NEW_PASSWORD}
    )
    old = await client.post(
        SESSION_START_PATH, json={"email": user.email.root, "password": "password"}
    )
    assert new.status_code == HTTPStatus.NO_CONTENT
    assert old.status_code == HTTPStatus.UNAUTHORIZED


async def test_an_address_with_no_user_gets_the_same_response_a_job_and_no_email(
    client: httpx.AsyncClient,
    worker_app: App,
    email_sender: FakeEmailSender,
    user: User,
) -> None:
    known = await client.post(REQUEST_PATH, json={"email": user.email.root})
    await worker_app.run_worker_async()
    email_sender.sent.clear()

    unknown = await client.post(REQUEST_PATH, json={"email": "nobody@example.com"})
    jobs = list(await worker_app.job_manager.list_jobs_async())
    await worker_app.run_worker_async()

    assert unknown.status_code == known.status_code == HTTPStatus.NO_CONTENT
    assert unknown.content == known.content == b""
    assert dict(unknown.headers) == dict(known.headers)
    assert len(jobs) == 2
    assert email_sender.sent == []
