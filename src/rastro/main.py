from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from rastro.api import api_router
from rastro.config import Settings, get_settings
from rastro.problem import install_exception_handlers
from rastro.security import SecurityHeadersMiddleware


def create_app(settings: Settings) -> FastAPI:
    # The API docs expose every route and schema, so only a debug build serves them.
    app = FastAPI(
        title="rastro",
        debug=settings.debug,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.debug else None,
    )

    # The middleware added last runs first: the host check rejects a request
    # before any other code sees it.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    install_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app(get_settings())
