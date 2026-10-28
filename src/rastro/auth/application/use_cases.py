from rastro.auth.application.dtos import (
    SessionGetOutput,
    SessionStartInput,
    SessionStartOutput,
    UserRegisterInput,
)
from rastro.auth.application.mappers import session_get_output, session_start_output
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
from rastro.auth.domain.value_objects import SessionLifetime, SessionToken
from rastro.common.domain.value_objects import TokenBytes


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
    lifetime: SessionLifetime,
    token_bytes: TokenBytes,
) -> SessionStartOutput:
    user = await users.get_by_email(input.email)
    check = password_hasher.verify(
        password=input.password, hashed=None if user is None else user.hashed_password
    )
    if user is None or not check.is_correct:
        raise IncorrectCredentialsError()
    if check.new_hash is not None:
        user.hashed_password = check.new_hash
        await users.update(user)
    token = SessionToken.generate(nbytes=token_bytes)
    session = Session.start(
        id=await sessions.next_id(),
        user_id=user.id,
        token=token,
        at=clock.now(),
        lifetime=lifetime,
    )
    await sessions.add(session)
    return session_start_output(session, token=token)


async def session_get(
    token: SessionToken | None,
    *,
    users: UserRepository,
    sessions: SessionRepository,
    clock: Clock,
) -> SessionGetOutput:
    session = await _active_session(token, sessions=sessions, clock=clock)
    user = await users.get_by_id(session.user_id)
    if user is None:
        # The foreign key deletes each Session with its User, so the User exists.
        raise LookupError(f"No User with the id {session.user_id.root}.")
    return session_get_output(user)


async def session_end(
    token: SessionToken | None, *, sessions: SessionRepository
) -> None:
    await sessions.remove(await _session(token, sessions=sessions))


async def _active_session(
    token: SessionToken | None, *, sessions: SessionRepository, clock: Clock
) -> Session:
    session = await _session(token, sessions=sessions)
    if not session.is_active(at=clock.now()):
        raise NotAuthenticatedError()
    return session


async def _session(
    token: SessionToken | None, *, sessions: SessionRepository
) -> Session:
    if token is None:
        raise NotAuthenticatedError()
    session = await sessions.get_by_hashed_token(token.digest())
    if session is None:
        raise NotAuthenticatedError()
    return session
