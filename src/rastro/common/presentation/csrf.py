import secrets
from http import HTTPStatus
from typing import Self

from fastapi import APIRouter, Depends, Request, Response
from pydantic import SecretStr

from rastro.common.domain.value_objects import RootValueObject, TokenBytes
from rastro.common.presentation.dependencies import AppSettings
from rastro.common.presentation.errors import CsrfFailedError
from rastro.settings import Settings

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class CsrfToken(RootValueObject[SecretStr]):
    @classmethod
    def generate(cls, *, nbytes: TokenBytes) -> Self:
        return cls(SecretStr(secrets.token_urlsafe(nbytes.root)))

    def matches(self, other: CsrfToken) -> bool:
        return secrets.compare_digest(
            self.root.get_secret_value().encode(),
            other.root.get_secret_value().encode(),
        )


def csrf_cookie_set(response: Response, *, settings: Settings) -> None:
    token = CsrfToken.generate(nbytes=settings.csrf_token_bytes)
    response.set_cookie(
        settings.csrf_cookie_name,
        token.root.get_secret_value(),
        secure=settings.csrf_cookie_secure,
        httponly=settings.csrf_cookie_httponly,
        samesite=settings.csrf_cookie_samesite.value,
    )


def csrf_check(request: Request, settings: AppSettings) -> None:
    if request.method in SAFE_METHODS:
        return
    cookie = request.cookies.get(settings.csrf_cookie_name)
    header = request.headers.get(settings.csrf_header_name)
    if not cookie or header is None:
        raise CsrfFailedError()
    expected = CsrfToken.model_validate(cookie)
    sent = CsrfToken.model_validate(header)
    if not expected.matches(sent):
        raise CsrfFailedError()


router = APIRouter(dependencies=[Depends(csrf_check)])


@router.get("/csrf", status_code=HTTPStatus.NO_CONTENT)
async def csrf_set_view(response: Response, settings: AppSettings) -> None:
    csrf_cookie_set(response, settings=settings)
