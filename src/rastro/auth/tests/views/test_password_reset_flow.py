from datetime import timedelta
from http import HTTPStatus

import httpx
from procrastinate import App
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User
from rastro.auth.infrastructure.models import ResetTokenRow
from rastro.auth.tests.fakes import FakeEmailSender

REQUEST_PATH = "/api/v1/auth/password-reset/request"
CONFIRM_PATH = "/api/v1/auth/password-reset/confirm"
SESSION_START_PATH = "/api/v1/auth/session/start"
NEW_PASSWORD = "newpassword"
INVALID_TOKEN = {"type": "auth.invalid_reset_token", "status": 400}


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


async def test_two_requests_within_the_cooldown_send_one_email_whose_token_works(
    client: httpx.AsyncClient,
    worker_app: App,
    email_sender: FakeEmailSender,
    user: User,
) -> None:
    first = await client.post(REQUEST_PATH, json={"email": user.email.root})
    second = await client.post(REQUEST_PATH, json={"email": user.email.root})
    await worker_app.run_worker_async()
    (email,) = email_sender.sent
    token = email_sender.last_reset_token().root.get_secret_value()

    confirmed = await client.post(
        CONFIRM_PATH, json={"token": token, "password": NEW_PASSWORD}
    )

    assert email.to == user.email
    assert second.status_code == first.status_code == HTTPStatus.NO_CONTENT
    assert second.content == first.content == b""
    assert dict(second.headers) == dict(first.headers)
    assert confirmed.status_code == HTTPStatus.NO_CONTENT


async def test_two_requests_past_the_cooldown_leave_only_the_second_link_working(
    client: httpx.AsyncClient,
    worker_app: App,
    email_sender: FakeEmailSender,
    db_session: AsyncSession,
    user: User,
) -> None:
    first = await client.post(REQUEST_PATH, json={"email": user.email.root})
    await worker_app.run_worker_async()
    first_token = email_sender.last_reset_token().root.get_secret_value()
    # The task reads the wall clock, so the row ages in place of the clock.
    await db_session.execute(
        update(ResetTokenRow).values(
            issued_at=ResetTokenRow.issued_at - timedelta(seconds=61)
        )
    )
    await db_session.commit()
    second = await client.post(REQUEST_PATH, json={"email": user.email.root})
    await worker_app.run_worker_async()
    second_token = email_sender.last_reset_token().root.get_secret_value()

    rejected = await client.post(
        CONFIRM_PATH, json={"token": first_token, "password": NEW_PASSWORD}
    )
    accepted = await client.post(
        CONFIRM_PATH, json={"token": second_token, "password": NEW_PASSWORD}
    )

    assert second.status_code == first.status_code == HTTPStatus.NO_CONTENT
    assert second.content == first.content == b""
    assert dict(second.headers) == dict(first.headers)
    assert len(email_sender.sent) == 2
    assert rejected.status_code == HTTPStatus.BAD_REQUEST
    assert rejected.json() == INVALID_TOKEN
    assert accepted.status_code == HTTPStatus.NO_CONTENT
