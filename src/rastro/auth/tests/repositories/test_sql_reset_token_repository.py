import asyncio
from collections.abc import Awaitable, Callable

import pydantic
import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, User
from rastro.auth.domain.ports import ResetTokenRepository, UserRepository
from rastro.auth.domain.value_objects import ResetToken
from rastro.auth.infrastructure.models import ResetTokenRow
from rastro.auth.infrastructure.repositories import SqlResetTokenRepository
from rastro.auth.tests.repositories.conftest import RESET_TOKEN_LIFETIME, START
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.common.tests.adapter import RepositoryKind


@pytest.fixture
def adapter() -> RepositoryKind:
    """The tests of this module run only on Postgres."""
    return RepositoryKind.SQL


async def test_a_consume_waits_for_a_concurrent_consume_and_then_finds_no_token(
    engine: AsyncEngine,
    committed_reset_token: IssuedResetToken,
    until_a_statement_waits: Callable[[str], Awaitable[None]],
) -> None:
    sessionmaker = create_sessionmaker(engine)
    digest = committed_reset_token.hashed_token

    async with sessionmaker() as first, sessionmaker() as second:
        consumed = await SqlResetTokenRepository(first).consume(digest)
        waiting = asyncio.create_task(SqlResetTokenRepository(second).consume(digest))
        await until_a_statement_waits("DELETE FROM auth_reset_token%")

        await first.commit()

        assert consumed == committed_reset_token
        assert await waiting is None
        await second.rollback()


async def test_a_consume_that_rolls_back_leaves_the_token_for_a_waiting_consume(
    engine: AsyncEngine,
    committed_reset_token: IssuedResetToken,
    until_a_statement_waits: Callable[[str], Awaitable[None]],
) -> None:
    sessionmaker = create_sessionmaker(engine)
    digest = committed_reset_token.hashed_token

    async with sessionmaker() as first, sessionmaker() as second:
        await SqlResetTokenRepository(first).consume(digest)
        waiting = asyncio.create_task(SqlResetTokenRepository(second).consume(digest))
        await until_a_statement_waits("DELETE FROM auth_reset_token%")

        await first.rollback()

        assert await waiting == committed_reset_token
        await second.rollback()


async def test_a_replace_waits_for_a_concurrent_replace_and_the_last_one_stays(
    engine: AsyncEngine,
    committed_reset_token: IssuedResetToken,
    until_a_statement_waits: Callable[[str], Awaitable[None]],
) -> None:
    sessionmaker = create_sessionmaker(engine)
    user_id = committed_reset_token.user_id

    async def issue(db_session: AsyncSession, *, token: str) -> IssuedResetToken:
        reset_tokens = SqlResetTokenRepository(db_session)
        return IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=user_id,
            token=ResetToken(SecretStr(token)),
            at=START,
            lifetime=RESET_TOKEN_LIFETIME,
        )

    async with sessionmaker() as first, sessionmaker() as second:
        earlier = await issue(first, token="earlier")
        last = await issue(second, token="last")
        await SqlResetTokenRepository(first).replace(earlier)
        waiting = asyncio.create_task(SqlResetTokenRepository(second).replace(last))
        await until_a_statement_waits("INSERT INTO auth_reset_token%")
        await first.commit()
        await waiting
        await second.commit()

    async with sessionmaker() as reader:
        assert await SqlResetTokenRepository(reader).get_by_user_id(user_id) == last


async def test_the_table_holds_one_row_per_user(
    db_session: AsyncSession,
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    newer_reset_token: IssuedResetToken,
) -> None:
    await reset_tokens.replace(issued_reset_token)

    db_session.add(
        ResetTokenRow(
            id=newer_reset_token.id.root,
            user_id=newer_reset_token.user_id.root,
            hashed_token=newer_reset_token.hashed_token.root,
            issued_at=newer_reset_token.issued_at,
            expires_at=newer_reset_token.expires_at,
        )
    )
    with pytest.raises(IntegrityError, match="auth_reset_token_user_id_key"):
        await db_session.flush()


async def test_the_row_of_a_reset_token_goes_away_with_its_user(
    db_session: AsyncSession,
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    ana: User,
) -> None:
    await reset_tokens.replace(issued_reset_token)

    await db_session.execute(
        text("DELETE FROM auth_user WHERE id = :id"), {"id": ana.id.root}
    )

    assert await reset_tokens.get_by_user_id(ana.id) is None


async def test_a_row_with_the_id_0_fails_to_become_a_reset_token(
    db_session: AsyncSession,
    reset_tokens: ResetTokenRepository,
    users: UserRepository,
    ana: User,
) -> None:
    await users.add(ana)
    await db_session.execute(
        text(
            "INSERT INTO auth_reset_token"
            " (id, user_id, hashed_token, issued_at, expires_at)"
            " VALUES (0, :user_id, 'x', now(), now())"
        ),
        {"user_id": ana.id.root},
    )

    with pytest.raises(pydantic.ValidationError):
        await reset_tokens.get_by_user_id(ana.id)


async def test_replace_leaves_created_at_and_updated_at_to_the_database(
    db_session: AsyncSession,
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
) -> None:
    await reset_tokens.replace(issued_reset_token)

    # now() is the start time of the transaction, so the row holds it exactly.
    audit = await db_session.execute(
        text(
            "SELECT created_at = now(), updated_at = now() FROM auth_reset_token"
            " WHERE id = :id"
        ),
        {"id": issued_reset_token.id.root},
    )
    assert tuple(audit.one()) == (True, True)


async def test_a_query_span_keeps_the_statement_and_no_parameters(
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    spans: InMemorySpanExporter,
) -> None:
    await reset_tokens.replace(issued_reset_token)
    await reset_tokens.consume(issued_reset_token.hashed_token)

    attributes = [dict(span.attributes or {}) for span in spans.get_finished_spans()]
    statements = [str(a["db.query.text"]) for a in attributes if "db.query.text" in a]
    assert any(s.startswith("INSERT INTO auth_reset_token ") for s in statements)
    assert any(s.startswith("DELETE FROM auth_reset_token ") for s in statements)
    assert repr(issued_reset_token.hashed_token.root) not in str(attributes)
