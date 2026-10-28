from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from taskiq import AsyncBroker

from rastro.auth.presentation.views import ERROR_STATUSES as AUTH_ERROR_STATUSES
from rastro.auth.presentation.views import router as auth_router
from rastro.common.presentation.problems import ERROR_STATUSES as COMMON_ERROR_STATUSES
from rastro.common.presentation.problems import ErrorStatuses, install_problem_handlers
from rastro.csrf.presentation.csrf_cookie import csrf_check
from rastro.csrf.presentation.views import ERROR_STATUSES as CSRF_ERROR_STATUSES
from rastro.csrf.presentation.views import router as csrf_router
from rastro.settings import Settings

CORS_METHODS = ["GET", "POST"]
CORS_HEADERS = ["Content-Type"]

ERROR_STATUSES: ErrorStatuses = {
    **COMMON_ERROR_STATUSES,
    **CSRF_ERROR_STATUSES,
    **AUTH_ERROR_STATUSES,
}
FRAME_HEADERS = {
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


class FrameHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_frame_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).update(FRAME_HEADERS)
            await send(message)

        await self.app(scope, receive, send_with_frame_headers)


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
        dependencies=[Depends(csrf_check)],
    )
    app.state.settings = settings
    app.state.sessionmaker = sessionmaker
    install_problem_handlers(app, error_statuses=ERROR_STATUSES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.root for origin in settings.cors_allowed_origins],
        allow_credentials=True,
        allow_methods=CORS_METHODS,
        allow_headers=[*CORS_HEADERS, settings.csrf_header_name],
    )
    app.add_middleware(FrameHeadersMiddleware)
    app.include_router(csrf_router, prefix="/api/v1/csrf")
    app.include_router(auth_router, prefix="/api/v1/auth")
    return app
