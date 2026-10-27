from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import PasswordCheck, Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    RawPassword,
    SessionToken,
)
from rastro.auth.tests.fakes import FakePasswordHasher
from rastro.common.domain.value_objects import Id

TEN_O_CLOCK = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
TOKEN = SessionToken(SecretStr("token"))


@pytest.fixture
def session() -> Session:
    return Session(
        id=Id(1), user_id=Id(2), hashed_token=TOKEN.digest(), expires_at=TEN_O_CLOCK
    )


def test_a_session_is_active_before_it_expires(session: Session) -> None:
    assert session.is_active(at=datetime(2026, 1, 1, 9, 59, tzinfo=UTC))


def test_a_session_is_not_active_from_the_moment_it_expires(session: Session) -> None:
    assert not session.is_active(at=TEN_O_CLOCK)


def test_a_session_starts_with_its_token_digest_and_ends_a_lifetime_later() -> None:
    session = Session.start(
        id=Id(1),
        user_id=Id(2),
        token=TOKEN,
        at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        lifetime=timedelta(hours=1),
    )

    assert session == Session(
        id=Id(1), user_id=Id(2), hashed_token=TOKEN.digest(), expires_at=TEN_O_CLOCK
    )


@pytest.mark.parametrize(
    ("hashed", "password", "check"),
    [
        ("fake$password", "password", PasswordCheck(True, needs_rehash=False)),
        ("outdated$password", "password", PasswordCheck(True, needs_rehash=True)),
        ("fake$password", "wrongpassword", PasswordCheck(False, needs_rehash=False)),
    ],
)
def test_verify_password_answers_whether_it_is_correct_and_needs_a_rehash(
    hashed: str, password: str, check: PasswordCheck
) -> None:
    user = User(
        id=Id(1),
        email=Email("ana@x.com"),
        display_name=DisplayName("Ana"),
        hashed_password=HashedPassword(hashed),
    )

    assert (
        user.verify_password(
            RawPassword(SecretStr(password)), hasher=FakePasswordHasher()
        )
        == check
    )
