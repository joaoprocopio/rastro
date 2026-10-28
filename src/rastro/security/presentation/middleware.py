from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

CORS_METHODS = ["GET", "POST"]
CORS_HEADERS = ["Content-Type"]
FRAME_HEADERS = {
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


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
