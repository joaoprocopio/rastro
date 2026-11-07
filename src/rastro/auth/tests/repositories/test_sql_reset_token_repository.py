import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

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
from rastro.auth.tests.conftest import until_a_statement_waits
from rastro.auth.tests.repositories.conftest import (
    RESET_TOKEN_COOLDOWN,
    RESET_TOKEN_LIFETIME,
    START,
)
from rastro.common.domain.value_objects import Id
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.common.tests.adapter import RepositoryKind

LATER = START + timedelta(hours=1)


@pytest.fixture
def adapter() -> RepositoryKind:
    """The tests of this module run only on Postgres."""
    return RepositoryKind.SQL


async def test_a_consume_waits_for_a_concurrent_consume_and_then_finds_no_token(
    engine: AsyncEngine, committed_reset_token: IssuedResetToken
) -> None:
    sessionmaker = create_sessionmaker(engine)
    digest = committed_reset_token.hashed_token

    async with (
        sessionmaker() as first,
        sessionmaker() as second,
        sessionmaker() as probe,
    ):
        consumed = await SqlResetTokenRepository(first).consume(digest)
        waiting = asyncio.create_task(SqlResetTokenRepository(second).consume(digest))
        await until_a_statement_waits(probe, statement="DELETE FROM auth_reset_token%")

        await first.commit()

        assert consumed == committed_reset_token
        assert await waiting is None
        await second.rollback()


async def test_a_consume_that_rolls_back_leaves_the_token_for_a_waiting_consume(
    engine: AsyncEngine, committed_reset_token: IssuedResetToken
) -> None:
    sessionmaker = create_sessionmaker(engine)
    digest = committed_reset_token.hashed_token

    async with (
        sessionmaker() as first,
        sessionmaker() as second,
        sessionmaker() as probe,
    ):
        await SqlResetTokenRepository(first).consume(digest)
        waiting = asyncio.create_task(SqlResetTokenRepository(second).consume(digest))
        await until_a_statement_waits(probe, statement="DELETE FROM auth_reset_token%")

        await first.rollback()

        assert await waiting == committed_reset_token
        await second.rollback()


async def _issue(
    db_session: AsyncSession, *, user_id: Id, token: str, at: datetime
) -> IssuedResetToken:
    reset_tokens = SqlResetTokenRepository(db_session)
    return IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=user_id,
        token=ResetToken(SecretStr(token)),
        at=at,
        lifetime=RESET_TOKEN_LIFETIME,
    )


@pytest.fixture(params=[False, True], ids=["no_stored_token", "old_stored_token"])
def raced_user_id(request: pytest.FixtureRequest, committed_user: User) -> Id:
    """The id of `committed_user`, with no Reset token or one older than the cooldown."""
    if request.param:
        request.getfixturevalue("committed_reset_token")
    return committed_user.id


@pytest.mark.parametrize(
    ("end_first", "second_at", "second_writes"),
    [
        pytest.param(
            AsyncSession.commit, LATER, False, id="commit_within_the_cooldown"
        ),
        pytest.param(
            AsyncSession.commit,
            LATER + RESET_TOKEN_COOLDOWN.root,
            True,
            id="commit_past_the_cooldown",
        ),
        pytest.param(AsyncSession.rollback, LATER, True, id="rollback"),
    ],
)
async def test_a_write_waits_for_a_concurrent_write_and_then_applies_the_cooldown_to_its_row(
    engine: AsyncEngine,
    raced_user_id: Id,
    end_first: Callable[[AsyncSession], Awaitable[None]],
    second_at: datetime,
    second_writes: bool,
) -> None:
    sessionmaker = create_sessionmaker(engine)

    async with (
        sessionmaker() as first,
        sessionmaker() as second,
        sessionmaker() as probe,
    ):
        first_token = await _issue(first, user_id=raced_user_id, token="1st", at=LATER)
        second_token = await _issue(
            second, user_id=raced_user_id, token="2nd", at=second_at
        )
        assert await SqlResetTokenRepository(first).replace_after_cooldown(
            first_token, cooldown=RESET_TOKEN_COOLDOWN
        )
        waiting = asyncio.create_task(
            SqlResetTokenRepository(second).replace_after_cooldown(
                second_token, cooldown=RESET_TOKEN_COOLDOWN
            )
        )
        await until_a_statement_waits(probe, statement="INSERT INTO auth_reset_token%")

        await end_first(first)

        assert await waiting is second_writes
        await second.commit()

    async with sessionmaker() as reader:
        stored = await SqlResetTokenRepository(reader).get_by_user_id(raced_user_id)
    assert stored == (second_token if second_writes else first_token)


async def test_the_table_holds_one_row_per_user(
    db_session: AsyncSession,
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
    newer_reset_token: IssuedResetToken,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

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
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

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


async def test_a_write_leaves_created_at_and_updated_at_to_the_database(
    db_session: AsyncSession,
    reset_tokens: ResetTokenRepository,
    issued_reset_token: IssuedResetToken,
) -> None:
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )

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
    await reset_tokens.replace_after_cooldown(
        issued_reset_token, cooldown=RESET_TOKEN_COOLDOWN
    )
    await reset_tokens.consume(issued_reset_token.hashed_token)

    attributes = [dict(span.attributes or {}) for span in spans.get_finished_spans()]
    statements = [str(a["db.query.text"]) for a in attributes if "db.query.text" in a]
    assert any(s.startswith("INSERT INTO auth_reset_token ") for s in statements)
    assert any(s.startswith("DELETE FROM auth_reset_token ") for s in statements)
    assert repr(issued_reset_token.hashed_token.root) not in str(attributes)
