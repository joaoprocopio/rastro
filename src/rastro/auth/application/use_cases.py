from datetime import timedelta

from rastro.auth.application.dtos import (
    SessionStartInput,
    UserGetCurrentOutput,
    UserRegisterInput,
)
from rastro.auth.application.mappers import user_get_current_output_from_user
from rastro.auth.domain.aggregates import Session, User
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


async def user_register(
    input: UserRegisterInput,
    *,
    users: UserRepository,
    password_hasher: PasswordHasher,
) -> None:
    if await users.get_by_email(input.email) is not None:
        raise EmailInUseError()
    await users.add(
        User(
            id=await users.next_id(),
            email=input.email,
            display_name=input.display_name,
            hashed_password=password_hasher.hash(password=input.password),
        )
    )


async def session_start(
    input: SessionStartInput,
    *,
    users: UserRepository,
    sessions: SessionRepository,
    password_hasher: PasswordHasher,
    clock: Clock,
    lifetime: timedelta,
    token_bytes: int,
) -> SessionToken:
    user = await users.get_by_email(input.email)
    if user is None:
        # An unknown email takes as long as a wrong password.
        password_hasher.verify(
            password=input.password, hashed=password_hasher.fixed_hash
        )
        raise IncorrectCredentialsError()
    check = user.verify_password(input.password, hasher=password_hasher)
    if not check.is_correct:
        raise IncorrectCredentialsError()
    if check.needs_rehash:
        user.hashed_password = password_hasher.hash(password=input.password)
        await users.update(user)
    token = SessionToken.generate(nbytes=token_bytes)
    await sessions.add(
        Session.start(
            id=await sessions.next_id(),
            user_id=user.id,
            token=token,
            at=clock.now(),
            lifetime=lifetime,
        )
    )
    return token


async def user_get_current(
    token: SessionToken | None,
    *,
    users: UserRepository,
    sessions: SessionRepository,
    clock: Clock,
) -> UserGetCurrentOutput:
    session = await _active_session(token, sessions=sessions, clock=clock)
    user = await users.get_by_id(session.user_id)
    if user is None:
        # The foreign key deletes each Session with its User, so the User exists.
        raise LookupError(f"No User with the id {session.user_id.root}.")
    return user_get_current_output_from_user(user)


async def session_end(
    token: SessionToken | None, *, sessions: SessionRepository, clock: Clock
) -> None:
    await sessions.remove(await _active_session(token, sessions=sessions, clock=clock))


async def _active_session(
    token: SessionToken | None, *, sessions: SessionRepository, clock: Clock
) -> Session:
    if token is None:
        raise NotAuthenticatedError()
    session = await sessions.get_by_token_hash(token.digest())
    if session is None or not session.is_active(at=clock.now()):
        raise NotAuthenticatedError()
    return session
