from rastro.auth.application.dtos import (
    PasswordResetConfirmInput,
    PasswordResetRequestInput,
    PasswordResetSendInput,
    SessionGetOutput,
    SessionRemoveExpiredOutput,
    SessionStartInput,
    SessionStartOutput,
    UserRegisterInput,
)
from rastro.auth.application.mappers import session_get_output, session_start_output
from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.errors import (
    EmailInUseError,
    IncorrectCredentialsError,
    InvalidResetTokenError,
    NotAuthenticatedError,
)
from rastro.auth.domain.ports import (
    Clock,
    EmailSender,
    PasswordHasher,
    PasswordResetJobs,
    ResetTokenRepository,
    SessionRepository,
    UserRepository,
)
from rastro.auth.domain.value_objects import (
    OutgoingEmail,
    ResetLinkUrl,
    ResetToken,
    ResetTokenLifetime,
    SessionLifetime,
    SessionToken,
)
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
    # The lock holds a confirmation back until the commit, as ADR 0002 records.
    user = await users.get_by_email_locked(input.email)
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
    await sessions.remove(await _stored_session(token, sessions=sessions))


async def session_remove_expired(
    *, sessions: SessionRepository, clock: Clock
) -> SessionRemoveExpiredOutput:
    return SessionRemoveExpiredOutput(
        count=await sessions.remove_expired(at=clock.now())
    )


async def password_reset_request(
    input: PasswordResetRequestInput, *, password_reset_jobs: PasswordResetJobs
) -> None:
    await password_reset_jobs.defer_send(input.email)


async def password_reset_send(
    input: PasswordResetSendInput,
    *,
    users: UserRepository,
    reset_tokens: ResetTokenRepository,
    email_sender: EmailSender,
    clock: Clock,
    lifetime: ResetTokenLifetime,
    token_bytes: TokenBytes,
    link_url: ResetLinkUrl,
) -> None:
    user = await users.get_by_email(input.email)
    if user is None:
        return
    token = ResetToken.generate(nbytes=token_bytes)
    await reset_tokens.replace(
        IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=user.id,
            token=token,
            at=clock.now(),
            lifetime=lifetime,
        )
    )
    await email_sender.send(
        OutgoingEmail.password_reset(
            to=user.email, link_url=link_url, token=token, lifetime=lifetime
        )
    )


async def password_reset_confirm(
    input: PasswordResetConfirmInput,
    *,
    users: UserRepository,
    sessions: SessionRepository,
    reset_tokens: ResetTokenRepository,
    password_hasher: PasswordHasher,
    clock: Clock,
) -> None:
    reset_token = await reset_tokens.consume(input.token.digest())
    if reset_token is None or reset_token.is_expired(at=clock.now()):
        raise InvalidResetTokenError()
    user = await users.get_by_id(reset_token.user_id)
    if user is None:
        # The foreign key deletes each Reset token with its User, so the User exists.
        raise LookupError(f"No User with the id {reset_token.user_id.root}.")
    user.hashed_password = password_hasher.hash(password=input.password)
    # The update waits for a sign-in that holds the row, so the next line removes its Session.
    await users.update(user)
    await sessions.remove_by_user_id(user.id)


async def _active_session(
    token: SessionToken | None, *, sessions: SessionRepository, clock: Clock
) -> Session:
    session = await _stored_session(token, sessions=sessions)
    if not session.is_active(at=clock.now()):
        raise NotAuthenticatedError()
    return session


async def _stored_session(
    token: SessionToken | None, *, sessions: SessionRepository
) -> Session:
    if token is None:
        raise NotAuthenticatedError()
    session = await sessions.get_by_hashed_token(token.digest())
    if session is None:
        raise NotAuthenticatedError()
    return session
