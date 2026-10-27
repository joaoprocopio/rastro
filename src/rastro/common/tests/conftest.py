from collections.abc import AsyncIterator, Awaitable, Callable

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from rastro.app import ERROR_STATUSES
from rastro.common.presentation.problems import install_problem_handlers
from rastro.common.presentation.views import CSRF_COOKIE, CSRF_HEADER
from rastro.common.tests.sample.infrastructure.models import NoteRow, SampleRow
from rastro.common.tests.sample.presentation.views import (
    ERROR_STATUSES as SAMPLE_ERROR_STATUSES,
)
from rastro.common.tests.sample.presentation.views import router


@pytest.fixture
async def sample_tables(connection: AsyncConnection) -> None:
    # The tables live in the test's transaction, so they vanish with its rollback.
    await connection.run_sync(SampleRow.metadata.create_all)


@pytest.fixture
def note_count(
    sessionmaker: async_sessionmaker[AsyncSession], sample_tables: None
) -> Callable[[], Awaitable[int]]:
    # A test reads the rows that a request or a task wrote, as the auth view tests do.
    async def count() -> int:
        async with sessionmaker() as db_session:
            count = await db_session.scalar(select(func.count()).select_from(NoteRow))
            if count is None:
                raise RuntimeError("COUNT returned no row.")
            return count

    return count


@pytest.fixture
def sample_app(app: FastAPI, sample_tables: None) -> FastAPI:
    app.include_router(router, prefix="/sample")
    install_problem_handlers(
        app, error_statuses={**ERROR_STATUSES, **SAMPLE_ERROR_STATUSES}
    )
    return app


@pytest.fixture
async def sample_client(
    sample_app: FastAPI, csrf_token: str
) -> AsyncIterator[httpx.AsyncClient]:
    # The 500 handler sends its response and then raises the exception again.
    transport = httpx.ASGITransport(app=sample_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://testserver",
        cookies={CSRF_COOKIE: csrf_token},
        headers={CSRF_HEADER: csrf_token},
    ) as client:
        yield client
