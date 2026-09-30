"""HTTP-level protections: CSRF tokens, security headers, and cookie names.

The CSRF defence is the signed double-submit cookie from the OWASP CSRF
Prevention Cheat Sheet. The server sets a token in a cookie that JavaScript can
read. The client echoes the token in the `X-CSRFToken` header on every unsafe
request. A cross-site page cannot read the cookie, so it cannot forge the
header. The token carries an HMAC over a nonce and the session token, so a
token stops validating once the session changes.
"""

import hashlib
import hmac
import secrets
from typing import Final, Literal

from fastapi import Request, Response
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from rastro.config import SettingsDep
from rastro.exceptions import CsrfError

SESSION_COOKIE_NAME: Final = "session"
CSRF_COOKIE_NAME: Final = "csrftoken"
CSRF_HEADER_NAME: Final = "X-CSRFToken"
SAFE_METHODS: Final = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# OWASP HTTP Headers and REST Security cheat sheets, for a JSON API
SECURITY_HEADERS: Final = (
    ("Cache-Control", "no-store"),
    ("Content-Security-Policy", "frame-ancestors 'none'"),
    ("Cross-Origin-Opener-Policy", "same-origin"),
    ("Referrer-Policy", "no-referrer"),
    ("Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
)

type SameSite = Literal["lax", "strict", "none"]


def set_cookie(
    response: Response,
    *,
    key: str,
    value: str,
    secure: bool,
    httponly: bool,
    samesite: SameSite = "lax",
) -> None:
    # No `max_age`: the browser drops the cookie when it closes, and the server
    # enforces the expiry on its own.
    response.set_cookie(
        key=key,
        value=value,
        path="/",
        secure=secure,
        httponly=httponly,
        samesite=samesite,
    )


def delete_cookie(
    response: Response, *, key: str, secure: bool, httponly: bool
) -> None:
    response.delete_cookie(
        key=key, path="/", secure=secure, httponly=httponly, samesite="lax"
    )


def _csrf_mac(secret: bytes, session_token: str, nonce: str) -> str:
    # The length prefixes keep ("ab", "c") and ("a", "bc") from signing alike.
    message = f"{len(session_token)}!{session_token}!{len(nonce)}!{nonce}"
    return hmac.new(secret, message.encode(), hashlib.sha256).hexdigest()


def issue_csrf_token(*, secret: bytes, session_token: str | None) -> str:
    nonce = secrets.token_urlsafe(32)
    return f"{nonce}.{_csrf_mac(secret, session_token or '', nonce)}"


def is_valid_csrf_token(
    token: str, *, secret: bytes, session_token: str | None
) -> bool:
    nonce, separator, mac = token.partition(".")
    if not separator:
        return False
    expected = _csrf_mac(secret, session_token or "", nonce)
    return hmac.compare_digest(mac, expected)


def set_csrf_cookie(
    response: Response, *, secret: bytes, session_token: str | None, secure: bool
) -> None:
    set_cookie(
        response,
        key=CSRF_COOKIE_NAME,
        value=issue_csrf_token(secret=secret, session_token=session_token),
        secure=secure,
        # the client reads the token from the cookie to echo it in the header
        httponly=False,
    )


def verify_csrf(request: Request, settings: SettingsDep) -> None:
    """Reject an unsafe request without a valid CSRF token or from a foreign origin."""
    if request.method in SAFE_METHODS:
        return

    origin = request.headers.get("origin")
    own_origin = f"{request.url.scheme}://{request.url.netloc}"
    if (
        origin is not None
        and origin != own_origin
        and origin not in settings.csrf_trusted_origins
    ):
        raise CsrfError(f"Origin {origin!r} is not trusted.")

    cookie = request.cookies.get(CSRF_COOKIE_NAME)
    header = request.headers.get(CSRF_HEADER_NAME)
    if cookie is None or header is None:
        raise CsrfError("The CSRF cookie or header is missing.")
    if not hmac.compare_digest(cookie, header):
        raise CsrfError("The CSRF header does not match the cookie.")

    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    secret = settings.secret_key.get_secret_value().encode()
    if not is_valid_csrf_token(header, secret=secret, session_token=session_token):
        raise CsrfError("The CSRF token is invalid.")


class SecurityHeadersMiddleware:
    """Add `SECURITY_HEADERS` to every HTTP response that does not set them.

    A plain ASGI middleware, so the response streams through unbuffered.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS:
                    headers.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)
