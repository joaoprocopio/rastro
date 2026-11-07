from http import HTTPStatus

import httpx
import pytest
from procrastinate import App
from procrastinate.testing import InMemoryConnector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User
from rastro.auth.presentation.tasks import PASSWORD_RESET_QUEUE
from rastro.settings import Settings

PATH = "/api/v1/auth/password-reset/request"
JOBS = text("SELECT queue_name, task_name, args FROM procrastinate_jobs ORDER BY id")
TASK = "auth:rastro.auth.presentation.tasks.password_reset_send_task"


async def test_a_known_and_an_unknown_address_get_the_same_response(
    client: httpx.AsyncClient, user: User
) -> None:
    known = await client.post(PATH, json={"email": user.email.root})
    unknown = await client.post(PATH, json={"email": "nobody@example.com"})

    assert known.status_code == unknown.status_code == HTTPStatus.NO_CONTENT
    assert known.content == unknown.content == b""
    assert dict(known.headers) == dict(unknown.headers)
    assert "Set-Cookie" not in known.headers


async def test_each_address_commits_one_job_on_the_queue_of_the_reset(
    client: httpx.AsyncClient, user: User, reader: AsyncSession
) -> None:
    await client.post(PATH, json={"email": " ANA@example.com "})
    await client.post(PATH, json={"email": "nobody@example.com"})

    jobs = await reader.execute(JOBS)
    assert [tuple(job) for job in jobs] == [
        (PASSWORD_RESET_QUEUE, TASK, {"email": "ana@example.com"}),
        (PASSWORD_RESET_QUEUE, TASK, {"email": "nobody@example.com"}),
    ]


@pytest.mark.parametrize(
    ("body", "problem"),
    [
        (
            {"email": "nope"},
            {"pointer": "#/email", "type": "request.invalid_format"},
        ),
        ({}, {"pointer": "#/email", "type": "request.field_required"}),
        (
            {"email": "ana@example.com", "extra": 1},
            {"pointer": "#/extra", "type": "request.unknown_field"},
        ),
    ],
)
async def test_a_malformed_body_is_a_validation_problem_and_defers_no_job(
    client: httpx.AsyncClient,
    reader: AsyncSession,
    body: dict[str, object],
    problem: dict[str, str],
) -> None:
    response = await client.post(PATH, json=body)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [problem],
    }
    assert list(await reader.execute(JOBS)) == []


async def test_an_email_with_a_lone_surrogate_is_a_validation_problem(
    client: httpx.AsyncClient, reader: AsyncSession
) -> None:
    # The JSON encoder of httpx rejects a lone surrogate, so the body stays literal.
    response = await client.post(
        PATH,
        content='{"email": "\\ud800@example.com"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#/email", "type": "request.invalid_format"}],
    }
    assert list(await reader.execute(JOBS)) == []


async def test_a_request_without_the_csrf_token_defers_no_job(
    client: httpx.AsyncClient, reader: AsyncSession, settings: Settings
) -> None:
    del client.headers[settings.csrf_header_name]

    response = await client.post(PATH, json={"email": "ana@example.com"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"type": "security.csrf_failed", "status": 403}
    assert list(await reader.execute(JOBS)) == []


async def test_the_job_of_a_request_reaches_the_connector_of_the_worker(
    client: httpx.AsyncClient, worker_app: App
) -> None:
    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)

    await client.post(PATH, json={"email": "ana@example.com"})

    (job,) = connector.jobs.values()
    assert job["args"] == {"email": "ana@example.com"}
