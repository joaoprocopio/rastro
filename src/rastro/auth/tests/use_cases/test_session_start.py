import pytest

from rastro.auth.application.dtos import SessionStartInput
from rastro.auth.application.use_cases import session_start
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import IncorrectCredentialsError
from rastro.auth.domain.value_objects import Email, HashedPassword, RawPassword
from rastro.auth.tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeSessionRepository,
    FakeUserRepository,
)

CORRECT = SessionStartInput(email=Email("ana@x.com"), password=RawPassword("password"))


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
    )

    assert sessions.sessions == {
        1: Session.start(id=1, user_id=ana.id, token=token, at=clock.now())
    }


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
    )
    second = await session_start(
        CORRECT,
        users=users,
        sessions=sessions,
        password_hasher=password_hasher,
        clock=clock,
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
            SessionStartInput(email=ana.email, password=RawPassword("wrongpassword")),
            users=users,
            sessions=sessions,
            password_hasher=password_hasher,
            clock=clock,
        )

    assert sessions.sessions == {}


async def test_an_unknown_email_verifies_against_the_fixed_hash_and_raises_the_same(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
) -> None:
    unknown = SessionStartInput(
        email=Email("nobody@x.com"), password=RawPassword("password")
    )

    with pytest.raises(IncorrectCredentialsError):
        await session_start(
            unknown,
            users=users,
            sessions=sessions,
            password_hasher=password_hasher,
            clock=clock,
        )

    assert password_hasher.verified == [
        (RawPassword("password"), password_hasher.fixed_hash)
    ]
    assert sessions.sessions == {}
