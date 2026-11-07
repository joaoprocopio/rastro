from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import IssuedResetToken, Session
from rastro.auth.domain.value_objects import (
    ResetToken,
    ResetTokenLifetime,
    SessionLifetime,
    SessionToken,
)
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
        lifetime=SessionLifetime(timedelta(hours=1)),
    )

    assert session == Session(
        id=Id(1), user_id=Id(2), hashed_token=TOKEN.digest(), expires_at=TEN_O_CLOCK
    )


def test_a_reset_token_is_issued_with_its_digest_and_expires_a_lifetime_later() -> None:
    nine_o_clock = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    token = ResetToken(SecretStr("token"))

    issued = IssuedResetToken.issue(
        id=Id(1),
        user_id=Id(2),
        token=token,
        at=nine_o_clock,
        lifetime=ResetTokenLifetime(timedelta(hours=1)),
    )

    assert issued == IssuedResetToken(
        id=Id(1),
        user_id=Id(2),
        hashed_token=token.digest(),
        issued_at=nine_o_clock,
        expires_at=TEN_O_CLOCK,
    )


def test_a_reset_token_is_not_expired_before_its_expiry(
    one_hour_reset_token: IssuedResetToken,
) -> None:
    before_its_expiry = one_hour_reset_token.expires_at - timedelta(seconds=1)

    assert not one_hour_reset_token.is_expired(at=before_its_expiry)


def test_a_reset_token_is_expired_from_the_moment_of_its_expiry(
    one_hour_reset_token: IssuedResetToken,
) -> None:
    assert one_hour_reset_token.is_expired(at=one_hour_reset_token.expires_at)
