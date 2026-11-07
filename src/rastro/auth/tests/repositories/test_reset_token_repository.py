from datetime import timedelta

from pydantic import SecretStr

from rastro.auth.domain.aggregates import IssuedResetToken, User
from rastro.auth.domain.ports import ResetTokenRepository, UserRepository
from rastro.auth.domain.value_objects import HashedResetToken, ResetToken
from rastro.auth.tests.repositories.conftest import RESET_TOKEN_LIFETIME, START

UNKNOWN_DIGEST = HashedResetToken(b"unknown")


async def test_get_by_user_id_reads_back_every_field_that_replace_wrote(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace(issued_reset_token)

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


async def test_replace_takes_the_place_of_the_reset_token_of_the_user(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    newer_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace(issued_reset_token)

    await reset_tokens.replace(newer_reset_token)

    assert await read_reset_tokens.get_by_user_id(ana.id) == newer_reset_token
    assert await reset_tokens.consume(issued_reset_token.hashed_token) is None


async def test_replace_keeps_the_reset_token_of_another_user(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    users: UserRepository,
    issued_reset_token: IssuedResetToken,
    bia: User,
) -> None:
    await users.add(bia)
    other = IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=bia.id,
        token=ResetToken(SecretStr("other")),
        at=START,
        lifetime=RESET_TOKEN_LIFETIME,
    )
    await reset_tokens.replace(other)

    await reset_tokens.replace(issued_reset_token)

    assert await read_reset_tokens.get_by_user_id(bia.id) == other


async def test_consume_returns_the_reset_token_and_removes_it(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace(issued_reset_token)

    consumed = await reset_tokens.consume(issued_reset_token.hashed_token)

    assert consumed == issued_reset_token
    assert await read_reset_tokens.get_by_user_id(ana.id) is None


async def test_a_second_consume_answers_none(
    reset_tokens: ResetTokenRepository, issued_reset_token: IssuedResetToken
) -> None:
    await reset_tokens.replace(issued_reset_token)
    await reset_tokens.consume(issued_reset_token.hashed_token)

    assert await reset_tokens.consume(issued_reset_token.hashed_token) is None


async def test_consume_of_an_unknown_digest_answers_none_and_keeps_the_others(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace(issued_reset_token)

    assert await reset_tokens.consume(UNKNOWN_DIGEST) is None
    assert await read_reset_tokens.get_by_user_id(ana.id) == issued_reset_token


async def test_a_field_assigned_with_no_replace_keeps_its_stored_value(
    reset_tokens: ResetTokenRepository,
    read_reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace(issued_reset_token)
    expires_at = issued_reset_token.expires_at
    issued_reset_token.expires_at -= timedelta(minutes=1)
    read = await read_reset_tokens.get_by_user_id(ana.id)
    assert read is not None
    read.expires_at -= timedelta(minutes=1)

    stored = await read_reset_tokens.get_by_user_id(ana.id)

    assert stored is not None
    assert stored.expires_at == expires_at
