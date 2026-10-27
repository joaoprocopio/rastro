from fastapi import Request, Response

from rastro.common.domain.value_objects import CsrfToken
from rastro.common.presentation.dependencies import AppSettings
from rastro.common.presentation.errors import CsrfFailedError
from rastro.settings import Settings

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def csrf_cookie_set(response: Response, *, settings: Settings) -> None:
    token = CsrfToken.generate(nbytes=settings.csrf_token_bytes)
    response.set_cookie(
        settings.csrf_cookie_name.root,
        token.root.get_secret_value(),
        secure=settings.csrf_cookie_secure,
        httponly=settings.csrf_cookie_httponly,
        samesite=settings.csrf_cookie_samesite.value,
    )


def csrf_check(request: Request, settings: AppSettings) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie = request.cookies.get(settings.csrf_cookie_name.root)
    header = request.headers.get(settings.csrf_header_name.root)
    if not cookie or header is None:
        raise CsrfFailedError()
    expected = CsrfToken.model_validate(cookie)
    sent = CsrfToken.model_validate(header)
    if not expected.matches(sent):
        raise CsrfFailedError()
