from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.application.dtos import PasswordResetConfirmInput
from rastro.auth.application.use_cases import password_reset_confirm
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import InvalidResetTokenError
from rastro.auth.domain.ports import PasswordHasher
from rastro.auth.domain.value_objects import (
    HashedPassword,
    RawPassword,
    ResetToken,
    SessionToken,
)
from rastro.auth.tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeResetTokenRepository,
    FakeSessionRepository,
    FakeUserRepository,
)
from rastro.auth.tests.use_cases.conftest import LIFETIME, RESET_TOKEN_LIFETIME

NEW_PASSWORD = RawPassword(SecretStr("newpassword"))


def _input(token: ResetToken) -> PasswordResetConfirmInput:
    return PasswordResetConfirmInput(token=token, password=NEW_PASSWORD)


async def test_it_stores_the_hash_of_the_new_password_and_removes_the_token(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: PasswordHasher,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
) -> None:
    await password_reset_confirm(
        _input(reset_token),
        users=users,
        sessions=sessions,
        reset_tokens=reset_tokens,
        password_hasher=password_hasher,
        clock=clock,
    )

    assert users.users[ana.id].hashed_password == HashedPassword("fake$newpassword")
    assert reset_tokens.reset_tokens == {}


async def test_it_removes_every_session_of_the_user_and_no_other(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: PasswordHasher,
    clock: FakeClock,
    ana: User,
    active_session: Session,
    expired_session: Session,
    reset_token: ResetToken,
) -> None:
    other = Session.start(
        id=await sessions.next_id(),
        user_id=await users.next_id(),
        token=SessionToken(SecretStr("other")),
        at=clock.now(),
        lifetime=LIFETIME,
    )
    await sessions.add(other)

    await password_reset_confirm(
        _input(reset_token),
        users=users,
        sessions=sessions,
        reset_tokens=reset_tokens,
        password_hasher=password_hasher,
        clock=clock,
    )

    assert sessions.sessions == {other.id: other}


async def test_a_used_token_raises_and_hashes_nothing(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
) -> None:
    await password_reset_confirm(
        _input(reset_token),
        users=users,
        sessions=sessions,
        reset_tokens=reset_tokens,
        password_hasher=password_hasher,
        clock=clock,
    )
    password_hasher.hashed.clear()
    hashed_password = users.users[ana.id].hashed_password

    with pytest.raises(InvalidResetTokenError):
        await password_reset_confirm(
            PasswordResetConfirmInput(
                token=reset_token, password=RawPassword(SecretStr("otherpassword"))
            ),
            users=users,
            sessions=sessions,
            reset_tokens=reset_tokens,
            password_hasher=password_hasher,
            clock=clock,
        )

    assert password_hasher.hashed == []
    assert users.users[ana.id].hashed_password == hashed_password


async def test_an_unknown_token_raises_and_hashes_nothing(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    reset_token: ResetToken,
    active_session: Session,
) -> None:
    with pytest.raises(InvalidResetTokenError):
        await password_reset_confirm(
            _input(ResetToken(SecretStr("unknown"))),
            users=users,
            sessions=sessions,
            reset_tokens=reset_tokens,
            password_hasher=password_hasher,
            clock=clock,
        )

    assert password_hasher.hashed == []
    assert len(sessions.sessions) == 1
    assert len(reset_tokens.reset_tokens) == 1


async def test_a_token_at_the_moment_of_its_expiry_raises_and_hashes_nothing(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
    active_session: Session,
) -> None:
    clock.current += RESET_TOKEN_LIFETIME.root

    with pytest.raises(InvalidResetTokenError):
        await password_reset_confirm(
            _input(reset_token),
            users=users,
            sessions=sessions,
            reset_tokens=reset_tokens,
            password_hasher=password_hasher,
            clock=clock,
        )

    assert password_hasher.hashed == []
    assert users.users[ana.id].hashed_password == HashedPassword("fake$password")
    assert len(sessions.sessions) == 1


async def test_a_token_one_second_before_its_expiry_works(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: PasswordHasher,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
) -> None:
    clock.current += RESET_TOKEN_LIFETIME.root - timedelta(seconds=1)

    await password_reset_confirm(
        _input(reset_token),
        users=users,
        sessions=sessions,
        reset_tokens=reset_tokens,
        password_hasher=password_hasher,
        clock=clock,
    )

    assert users.users[ana.id].hashed_password == HashedPassword("fake$newpassword")


async def test_a_token_whose_user_is_gone_breaks_an_invariant(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    reset_tokens: FakeResetTokenRepository,
    password_hasher: PasswordHasher,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
) -> None:
    del users.users[ana.id]

    with pytest.raises(LookupError, match=f"with the id {ana.id.root}\\."):
        await password_reset_confirm(
            _input(reset_token),
            users=users,
            sessions=sessions,
            reset_tokens=reset_tokens,
            password_hasher=password_hasher,
            clock=clock,
        )
