from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import IssuedResetToken, User
from rastro.auth.domain.ports import ResetTokenRepository, UserRepository
from rastro.auth.domain.value_objects import (
    HashedResetToken,
    ResetToken,
    ResetTokenCooldown,
)
from rastro.auth.tests.repositories.conftest import (
    RESET_TOKEN_COOLDOWN,
    RESET_TOKEN_LIFETIME,
)

UNKNOWN_DIGEST = HashedResetToken(b"unknown")


async def test_get_by_user_id_reads_back_every_field_of_the_stored_reset_token(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token


async def test_get_by_user_id_answers_none_for_a_user_with_no_reset_token(
    reset_tokens: ResetTokenRepository, ana: User, users: UserRepository
) -> None:
    await users.add(ana)

    assert await reset_tokens.get_by_user_id(ana.id) is None


async def test_two_next_id_calls_return_two_different_ids(
    reset_tokens: ResetTokenRepository,
) -> None:
    assert await reset_tokens.next_id() != await reset_tokens.next_id()


async def test_a_first_write_stores_the_reset_token_and_reports_that_it_wrote(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    wrote = await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    assert wrote is True
    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token


async def test_a_write_after_the_cooldown_takes_the_place_of_the_reset_token_of_the_user(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    newer_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    wrote = await reset_tokens.replace_after_cooldown(
        newer_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    assert wrote is True
    assert await read_reset_tokens.get_by_user_id(ana.id) == newer_reset_token
    assert await reset_tokens.consume(issued_reset_token.hashed_token) is None


@pytest.mark.parametrize(
    ("elapsed", "writes"),
    [
        pytest.param(
            RESET_TOKEN_COOLDOWN.root - timedelta(microseconds=1),
            False,
            id="one_microsecond_before_the_end",
        ),
        pytest.param(RESET_TOKEN_COOLDOWN.root, True, id="at_the_end"),
    ],
)
async def test_a_write_and_is_younger_than_agree_at_the_end_of_the_cooldown(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
    elapsed: timedelta,
    writes: bool,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    later = IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=ana.id,
        token=ResetToken(SecretStr("later")),
        at=issued_reset_token.issued_at + elapsed,
        lifetime=RESET_TOKEN_LIFETIME,
    )

    wrote = await reset_tokens.replace_after_cooldown(
        later, cooldown=RESET_TOKEN_COOLDOWN
    )

    assert wrote is writes
    assert issued_reset_token.is_younger_than(
        RESET_TOKEN_COOLDOWN, at=later.issued_at
    ) is (not writes)
    stored = await read_reset_tokens.get_by_user_id(ana.id)
    assert stored == (later if writes else issued_reset_token)


async def test_a_write_applies_the_cooldown_it_receives(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    newer_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    # `newer_reset_token` comes one hour after `issued_reset_token`.
    wrote = await reset_tokens.replace_after_cooldown(
        newer_reset_token, cooldown=ResetTokenCooldown(timedelta(hours=2))
    )

    assert wrote is False
    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token


async def test_a_write_keeps_the_reset_token_of_another_user(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    earlier_reset_token: IssuedResetToken,
    bia: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        earlier_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    assert await read_reset_tokens.get_by_user_id(bia.id) == earlier_reset_token


async def test_consume_returns_the_reset_token_and_removes_it(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    consumed = await reset_tokens.consume(issued_reset_token.hashed_token)

    assert consumed == issued_reset_token
    assert await read_reset_tokens.get_by_user_id(ana.id) is None


async def test_a_second_consume_answers_none(
    reset_tokens: ResetTokenRepository, issued_reset_token: IssuedResetToken
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    await reset_tokens.consume(issued_reset_token.hashed_token)

    assert await reset_tokens.consume(issued_reset_token.hashed_token) is None


async def test_consume_of_an_unknown_digest_answers_none_and_keeps_the_others(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    assert await reset_tokens.consume(UNKNOWN_DIGEST) is None
    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token


async def test_remove_expired_removes_an_expired_reset_token_and_keeps_a_valid_one(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    earlier_reset_token: IssuedResetToken,
    ana: User,
    bia: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    await reset_tokens.replace_after_cooldown(
        earlier_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    await reset_tokens.remove_expired(
        at=issued_reset_token.expires_at - timedelta(seconds=1)
    )

    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token
    assert await read_reset_tokens.get_by_user_id(bia.id) is None


async def test_remove_expired_removes_a_reset_token_that_expires_at_that_moment(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    await reset_tokens.remove_expired(at=issued_reset_token.expires_at)

    assert await read_reset_tokens.get_by_user_id(ana.id) is None


async def test_remove_expired_keeps_every_valid_reset_token_and_returns_0(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    earlier_reset_token: IssuedResetToken,
    ana: User,
    bia: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    await reset_tokens.replace_after_cooldown(
        earlier_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    removed = await reset_tokens.remove_expired(
        at=earlier_reset_token.expires_at - timedelta(seconds=1)
    )

    assert removed == 0
    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token
    assert await read_reset_tokens.get_by_user_id(bia.id) == earlier_reset_token


async def test_remove_expired_returns_the_number_of_removed_reset_tokens(
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    earlier_reset_token: IssuedResetToken,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    await reset_tokens.replace_after_cooldown(
        earlier_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

    removed = await reset_tokens.remove_expired(at=issued_reset_token.expires_at)

    assert removed == 2


async def test_a_field_assigned_with_no_write_keeps_its_stored_value(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    expires_at = issued_reset_token.expires_at
    issued_reset_token.expires_at -= timedelta(minutes=1)
    read = await read_reset_tokens.get_by_user_id(ana.id)
    assert read is not None
    read.expires_at -= timedelta(minutes=1)

    stored = await read_reset_tokens.get_by_user_id(ana.id)

    assert stored is not None
    assert stored.expires_at == expires_at
