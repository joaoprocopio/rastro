from typing import Annotated

from fastapi import Depends, Request, Response

from rastro.auth.domain.value_objects import SessionToken
from rastro.common.presentation.dependencies import AppSettings
from rastro.settings import Settings


def session_cookie_set(
    response: Response, token: SessionToken, *, settings: Settings
) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token.root.get_secret_value(),
        max_age=int(settings.session_lifetime.root.total_seconds()),
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite.value,
    )


def session_cookie_delete(response: Response, *, settings: Settings) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite.value,
    )


def _session_token(request: Request, settings: AppSettings) -> SessionToken | None:
    value = request.cookies.get(settings.session_cookie_name)
    return None if value is None else SessionToken.model_validate(value)


CurrentSessionToken = Annotated[SessionToken | None, Depends(_session_token)]
