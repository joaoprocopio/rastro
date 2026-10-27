import secrets

from fastapi import Request, Response

from rastro.common.domain.value_objects import CsrfToken
from rastro.common.presentation.dependencies import AppSettings
from rastro.common.presentation.errors import CsrfFailedError
from rastro.settings import Settings

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def csrf_cookie_set(response: Response, *, settings: Settings) -> None:
    token = CsrfToken.generate(nbytes=settings.csrf_token_bytes)
    response.set_cookie(
        settings.csrf_cookie_name,
        token.root.get_secret_value(),
        secure=settings.csrf_cookie_secure,
        httponly=settings.csrf_cookie_httponly,
        samesite=settings.csrf_cookie_samesite,
    )


def csrf_check(request: Request, settings: AppSettings) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie = request.cookies.get(settings.csrf_cookie_name)
    header = request.headers.get(settings.csrf_header_name)
    if not cookie or header is None:
        raise CsrfFailedError()
    expected = CsrfToken.model_validate(cookie).root.get_secret_value()
    sent = CsrfToken.model_validate(header).root.get_secret_value()
    if not secrets.compare_digest(expected.encode(), sent.encode()):
        raise CsrfFailedError()
