from datetime import UTC, datetime

import pydantic
import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User
from rastro.auth.domain.value_objects import DisplayName, Email, HashedPassword
from rastro.auth.infrastructure.repositories import SqlUserRepository
from rastro.common.domain.value_objects import Id


async def _ada(users: SqlUserRepository) -> User:
    return User(
        id=await users.next_id(),
        email=Email("ada@x.com"),
        display_name=DisplayName("Ada"),
        hashed_password=HashedPassword("fake$supersecret"),
    )


async def test_a_row_whose_email_breaks_its_value_object_fails_to_become_a_user(
    db_session: AsyncSession,
) -> None:
    now = datetime.now(UTC)
    await db_session.execute(
        text(
            "INSERT INTO auth_user"
            " (id, email, display_name, hashed_password, created_at, updated_at)"
            " VALUES (1, 'not-an-email', 'Ana', 'fake$x', :now, :now)"
        ),
        {"now": now},
    )

    with pytest.raises(pydantic.ValidationError):
        await SqlUserRepository(db_session).get_by_id(Id(1))


async def test_a_row_with_the_id_0_fails_to_become_a_user(
    db_session: AsyncSession,
) -> None:
    now = datetime.now(UTC)
    await db_session.execute(
        text(
            "INSERT INTO auth_user"
            " (id, email, display_name, hashed_password, created_at, updated_at)"
            " VALUES (0, 'ana@x.com', 'Ana', 'fake$x', :now, :now)"
        ),
        {"now": now},
    )

    with pytest.raises(pydantic.ValidationError):
        await SqlUserRepository(db_session).get_by_email(Email("ana@x.com"))


async def test_add_leaves_created_at_and_updated_at_to_the_database(
    db_session: AsyncSession,
) -> None:
    users = SqlUserRepository(db_session)
    ada = await _ada(users)

    await users.add(ada)

    # now() is the start time of the transaction, so the row holds it exactly.
    audit = await db_session.execute(
        text(
            "SELECT created_at = now(), updated_at = now() FROM auth_user"
            " WHERE id = :id"
        ),
        {"id": ada.id.root},
    )
    assert tuple(audit.one()) == (True, True)


async def test_a_query_span_keeps_the_statement_and_no_parameters(
    db_session: AsyncSession, spans: InMemorySpanExporter
) -> None:
    users = SqlUserRepository(db_session)

    await users.add(await _ada(users))

    attributes = [dict(span.attributes or {}) for span in spans.get_finished_spans()]
    statements = [str(a["db.statement"]) for a in attributes if "db.statement" in a]
    assert any(s.startswith("INSERT INTO auth_user ") for s in statements)
    assert "fake$supersecret" not in str(attributes)
    assert "ada@x.com" not in str(attributes)
