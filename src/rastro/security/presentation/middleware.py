from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from rastro.settings import Settings

FRAME_HEADERS = {
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


def cors(app: ASGIApp, *, settings: Settings) -> ASGIApp:
    return CORSMiddleware(
        app,
        allow_origins=[str(origin) for origin in settings.cors_allowed_origins],
        allow_origin_regex="|".join(
            f"(?:{regex.pattern})" for regex in settings.cors_allowed_origin_regexes
        )
        or None,
        allow_credentials=settings.cors_allow_credentials,
        allow_private_network=settings.cors_allow_private_network,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=settings.cors_expose_headers,
        max_age=int(settings.cors_preflight_max_age.total_seconds()),
    )


def frame_headers(app: ASGIApp) -> ASGIApp:
    async def app_with_frame_headers(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        async def send_with_frame_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).update(FRAME_HEADERS)
            await send(message)

        await app(scope, receive, send_with_frame_headers)

    return app_with_frame_headers
