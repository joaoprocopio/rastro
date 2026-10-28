from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from taskiq import AsyncBroker

from rastro.auth.presentation.views import ERROR_STATUSES as AUTH_ERROR_STATUSES
from rastro.auth.presentation.views import router as auth_router
from rastro.common.presentation.csrf import router as csrf_router
from rastro.common.presentation.problems import ERROR_STATUSES as COMMON_ERROR_STATUSES
from rastro.common.presentation.problems import ErrorStatuses, install_problem_handlers
from rastro.settings import Settings

ERROR_STATUSES: ErrorStatuses = {**COMMON_ERROR_STATUSES, **AUTH_ERROR_STATUSES}


def create_app(
    *,
    settings: Settings,
    sessionmaker: async_sessionmaker[AsyncSession],
    broker: AsyncBroker,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        # The broker of a process that sends tasks opens its connection here.
        async with broker:
            yield

    # openapi_url=None also turns off the /docs and /redoc pages.
    app = FastAPI(
        title="rastro",
        openapi_url="/openapi.json" if settings.openapi_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.sessionmaker = sessionmaker
    install_problem_handlers(app, error_statuses=ERROR_STATUSES)
    app.include_router(csrf_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1/auth")
    return app
