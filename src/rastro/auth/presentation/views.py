from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from rastro.auth.application import use_cases
from rastro.auth.application.dtos import (
    SessionStartInput,
    UserGetCurrentOutput,
    UserRegisterInput,
)
from rastro.auth.domain.aggregates import SESSION_LIFETIME
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

SESSION_COOKIE = "rastro_session"

ERROR_STATUSES: ErrorStatuses = {
    EmailInUseError: HTTPStatus.CONFLICT,
    IncorrectCredentialsError: HTTPStatus.UNAUTHORIZED,
    NotAuthenticatedError: HTTPStatus.UNAUTHORIZED,
}

router = APIRouter(dependencies=[Depends(csrf_check)])


def _session_token(request: Request) -> SessionToken | None:
    value = request.cookies.get(SESSION_COOKIE)
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
    response: Response,
) -> None:
    token = await use_cases.session_start(
        body,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
    )
    response.set_cookie(
        SESSION_COOKIE,
        token.root,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
    )


@router.get("/session")
async def user_get_current_view(
    token: CurrentSessionToken,
    users: Annotated[UserRepository, Depends(dependencies.user_repository)],
    sessions: Annotated[SessionRepository, Depends(dependencies.session_repository)],
    clock: Annotated[Clock, Depends(dependencies.clock)],
) -> UserGetCurrentOutput:
    return await use_cases.user_get_current(
        token, users=users, sessions=sessions, clock=clock
    )


@router.post("/session/end", status_code=HTTPStatus.NO_CONTENT)
async def session_end_view(
    token: CurrentSessionToken,
    sessions: Annotated[SessionRepository, Depends(dependencies.session_repository)],
    clock: Annotated[Clock, Depends(dependencies.clock)],
    response: Response,
) -> None:
    await use_cases.session_end(token, sessions=sessions, clock=clock)
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=True, samesite="lax")


@router.get("/csrf", status_code=HTTPStatus.NO_CONTENT)
async def csrf_set_view(response: Response, settings: AppSettings) -> None:
    csrf_cookie_set(response, settings=settings)
