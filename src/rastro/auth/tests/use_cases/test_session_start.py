from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.application.dtos import SessionStartInput
from rastro.auth.application.use_cases import session_start
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import IncorrectCredentialsError
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    RawPassword,
    SessionLifetime,
)
from rastro.auth.tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeSessionRepository,
    FakeUserRepository,
)
from rastro.common.domain.value_objects import Id, TokenBytes

LIFETIME = SessionLifetime(timedelta(hours=1))
TOKEN_BYTES = TokenBytes(16)
CORRECT = SessionStartInput(
    email=Email("ana@x.com"), password=RawPassword(SecretStr("password"))
)


async def test_correct_credentials_start_a_session_of_the_user_for_the_token(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
) -> None:
    token = await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=LIFETIME,
        token_bytes=TOKEN_BYTES,
    )

    assert sessions.sessions == {
        Id(1): Session(
            id=Id(1),
            user_id=ana.id,
            hashed_token=token.digest(),
            expires_at=clock.now() + timedelta(hours=1),
        )
    }


async def test_the_token_has_the_number_of_bytes_that_the_use_case_receives(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
) -> None:
    token = await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=LIFETIME,
        token_bytes=TOKEN_BYTES,
    )

    # 16 bytes in URL-safe base64 with no padding.
    assert len(token.root.get_secret_value()) == 22


async def test_each_session_gets_a_new_token(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
) -> None:
    first = await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=LIFETIME,
        token_bytes=TOKEN_BYTES,
    )
    second = await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=LIFETIME,
        token_bytes=TOKEN_BYTES,
    )

    assert first != second


async def test_a_correct_sign_in_stores_a_new_hash_for_an_outdated_one(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
) -> None:
    ana.hashed_password = HashedPassword("outdated$password")
    await users.update(ana)

    await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=LIFETIME,
        token_bytes=TOKEN_BYTES,
    )

    assert users.users[ana.id].hashed_password == HashedPassword("fake$password")


async def test_a_correct_sign_in_keeps_a_current_hash(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
) -> None:
    await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
        lifetime=LIFETIME,
        token_bytes=TOKEN_BYTES,
    )

    assert password_hasher.hashed == []
    assert users.users == {ana.id: ana}


async def test_a_wrong_password_raises_and_starts_no_session(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
    ana: User,
) -> None:
    with pytest.raises(IncorrectCredentialsError):
        await session_start(
            SessionStartInput(
                email=ana.email, password=RawPassword(SecretStr("wrongpassword"))
            ),
            users=users,
            sessions=sessions,
            password_hasher=password_hasher,
            clock=clock,
            lifetime=LIFETIME,
            token_bytes=TOKEN_BYTES,
        )

    assert sessions.sessions == {}


async def test_an_unknown_email_verifies_with_no_hash_and_raises_the_same(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
) -> None:
    unknown = SessionStartInput(
        email=Email("nobody@x.com"), password=RawPassword(SecretStr("password"))
    )

    with pytest.raises(IncorrectCredentialsError):
        await session_start(
            unknown,
            users=users,
            sessions=sessions,
            password_hasher=password_hasher,
            clock=clock,
            lifetime=LIFETIME,
            token_bytes=TOKEN_BYTES,
        )

    assert password_hasher.verified == [(RawPassword(SecretStr("password")), None)]
    assert sessions.sessions == {}
