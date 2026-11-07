from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from rastro.auth.application import use_cases
from rastro.auth.application.dtos import (
    PasswordResetConfirmInput,
    PasswordResetRequestInput,
    SessionGetOutput,
    SessionStartInput,
    UserRegisterInput,
)
from rastro.auth.domain.errors import (
    EmailInUseError,
    IncorrectCredentialsError,
    InvalidResetTokenError,
    NotAuthenticatedError,
)
from rastro.auth.domain.ports import (
    Clock,
    PasswordHasher,
    PasswordResetJobs,
    ResetTokenRepository,
    SessionRepository,
    UserRepository,
)
from rastro.auth.presentation import dependencies, tasks
from rastro.auth.presentation.session_cookie import (
    CurrentSessionToken,
    session_cookie_delete,
    session_cookie_set,
)
from rastro.common.presentation.dependencies import AppSettings
from rastro.common.presentation.problems import ErrorStatuses

ERROR_STATUSES: ErrorStatuses = {
    EmailInUseError: HTTPStatus.CONFLICT,
    IncorrectCredentialsError: HTTPStatus.UNAUTHORIZED,
    InvalidResetTokenError: HTTPStatus.BAD_REQUEST,
    NotAuthenticatedError: HTTPStatus.UNAUTHORIZED,
}

router = APIRouter()


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
    output = await use_cases.session_start(
        body,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=settings.session_lifetime,
        token_bytes=settings.session_token_bytes,
    )
    session_cookie_set(response, output=output, settings=settings)


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
    settings: AppSettings,
    response: Response,
) -> None:
    await use_cases.session_end(token, sessions=sessions)
    session_cookie_delete(response, settings=settings)


@router.post("/password-reset/request", status_code=HTTPStatus.NO_CONTENT)
async def password_reset_request_view(
    body: PasswordResetRequestInput,
    password_reset_jobs: Annotated[
        PasswordResetJobs, Depends(tasks.password_reset_jobs)
    ],
) -> None:
    await use_cases.password_reset_request(
        body, password_reset_jobs=password_reset_jobs
    )


@router.post("/password-reset/confirm", status_code=HTTPStatus.NO_CONTENT)
async def password_reset_confirm_view(
    body: PasswordResetConfirmInput,
    users: Annotated[UserRepository, Depends(dependencies.user_repository)],
    sessions: Annotated[SessionRepository, Depends(dependencies.session_repository)],
    reset_tokens: Annotated[
        ResetTokenRepository, Depends(dependencies.reset_token_repository)
    ],
    password_hasher: Annotated[PasswordHasher, Depends(dependencies.password_hasher)],
    clock: Annotated[Clock, Depends(dependencies.clock)],
) -> None:
    await use_cases.password_reset_confirm(
        body,
        users=users,
        sessions=sessions,
        reset_tokens=reset_tokens,
        password_hasher=password_hasher,
        clock=clock,
    )
