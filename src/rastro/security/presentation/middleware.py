from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from rastro.settings import Settings

CORS_METHODS = ["GET", "POST"]
CORS_HEADERS = ["Content-Type"]
FRAME_HEADERS = {
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


def cors(app: ASGIApp, *, settings: Settings) -> ASGIApp:
    return CORSMiddleware(
        app,
        allow_origins=[str(origin) for origin in settings.cors_allowed_origins],
        allow_credentials=True,
        allow_methods=CORS_METHODS,
        allow_headers=[*CORS_HEADERS, settings.csrf_header_name],
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
