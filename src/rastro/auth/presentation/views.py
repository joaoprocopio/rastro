from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from rastro.auth.application import use_cases
from rastro.auth.application.dtos import (
    SessionGetOutput,
    SessionStartInput,
    UserRegisterInput,
)
from rastro.auth.domain.errors import (
    EmailInUseError,
    IncorrectCredentialsError,
    NotAuthenticatedError,
)
from rastro.auth.domain.ports import (
    Clock,
    PasswordHasher,
    SessionRepository,
    UserRepository,
)
from rastro.auth.domain.value_objects import SessionToken
from rastro.auth.presentation import dependencies
from rastro.common.presentation.dependencies import AppSettings
from rastro.common.presentation.problems import ErrorStatuses
from rastro.common.presentation.views import csrf_check, csrf_cookie_set

ERROR_STATUSES: ErrorStatuses = {
    EmailInUseError: HTTPStatus.CONFLICT,
    IncorrectCredentialsError: HTTPStatus.UNAUTHORIZED,
    NotAuthenticatedError: HTTPStatus.UNAUTHORIZED,
}

router = APIRouter(dependencies=[Depends(csrf_check)])


def _session_token(request: Request, settings: AppSettings) -> SessionToken | None:
    value = request.cookies.get(settings.session_cookie_name.root)
    return None if value is None else SessionToken.model_validate(value)


CurrentSessionToken = Annotated[SessionToken | None, Depends(_session_token)]


@router.post("/register", status_code=HTTPStatus.CREATED, response_class=Response)
async def user_register_view(
    body: UserRegisterInput,
    users: Annotated[UserRepository, Depends(dependencies.user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(dependencies.password_hasher)],
) -> None:
    await use_cases.user_register(body, users=users, password_hasher=password_hasher)


@router.post("/session/start", status_code=HTTPStatus.NO_CONTENT)
async def session_start_view(
    body: SessionStartInput,
    users: Annotated[UserRepository, Depends(dependencies.user_repository)],
    sessions: Annotated[SessionRepository, Depends(dependencies.session_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(dependencies.password_hasher)],
    clock: Annotated[Clock, Depends(dependencies.clock)],
    settings: AppSettings,
    response: Response,
) -> None:
    token = await use_cases.session_start(
        body,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=settings.session_lifetime,
        token_bytes=settings.session_token_bytes,
    )
    response.set_cookie(
        settings.session_cookie_name.root,
        token.root.get_secret_value(),
        max_age=int(settings.session_lifetime.root.total_seconds()),
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite.value,
    )


@router.get("/session")
async def session_get_view(
    token: CurrentSessionToken,
    users: Annotated[UserRepository, Depends(dependencies.user_repository)],
    sessions: Annotated[SessionRepository, Depends(dependencies.session_repository)],
    clock: Annotated[Clock, Depends(dependencies.clock)],
) -> SessionGetOutput:
    return await use_cases.session_get(
        token, users=users, sessions=sessions, clock=clock
    )


@router.post("/session/end", status_code=HTTPStatus.NO_CONTENT)
async def session_end_view(
    token: CurrentSessionToken,
    sessions: Annotated[SessionRepository, Depends(dependencies.session_repository)],
    clock: Annotated[Clock, Depends(dependencies.clock)],
    settings: AppSettings,
    response: Response,
) -> None:
    await use_cases.session_end(token, sessions=sessions, clock=clock)
    response.delete_cookie(
        settings.session_cookie_name.root,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite.value,
    )


@router.get("/csrf", status_code=HTTPStatus.NO_CONTENT)
async def csrf_set_view(response: Response, settings: AppSettings) -> None:
    csrf_cookie_set(response, settings=settings)
