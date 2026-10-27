import secrets

from fastapi import Request, Response

from rastro.common.presentation.errors import CsrfFailedError

CSRF_COOKIE = "rastro_csrf"
CSRF_HEADER = "X-CSRF-Token"
CSRF_TOKEN_BYTES = 32
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def csrf_cookie_set(response: Response) -> None:
    # Scripts read the token to send it back, so the cookie is not HttpOnly.
    response.set_cookie(
        CSRF_COOKIE,
        secrets.token_urlsafe(CSRF_TOKEN_BYTES),
        secure=True,
        samesite="lax",
    )


def csrf_check(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or header is None:
        raise CsrfFailedError()
    if not secrets.compare_digest(cookie.encode(), header.encode()):
        raise CsrfFailedError()
