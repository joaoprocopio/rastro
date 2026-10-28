import pydantic
import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User
from rastro.auth.domain.ports import UserRepository
from rastro.auth.domain.value_objects import Email
from rastro.auth.infrastructure.repositories import SqlUserRepository
from rastro.common.domain.value_objects import Id
from rastro.common.tests.adapter import Adapter

INSERT_USER = text(
    "INSERT INTO auth_user"
    " (id, email, display_name, hashed_password, created_at, updated_at)"
    " VALUES (:id, :email, 'Ana', 'fake$x', now(), now())"
)


@pytest.fixture
def adapter() -> Adapter:
    """The tests of this module run only on Postgres."""
    return Adapter.SQL


async def test_a_row_whose_email_breaks_its_value_object_fails_to_become_a_user(
    db_session: AsyncSession,
) -> None:
    await db_session.execute(INSERT_USER, {"id": 1, "email": "not-an-email"})

    with pytest.raises(pydantic.ValidationError):
        await SqlUserRepository(db_session).get_by_id(Id(1))


async def test_a_row_with_the_id_0_fails_to_become_a_user(
    db_session: AsyncSession,
) -> None:
    await db_session.execute(INSERT_USER, {"id": 0, "email": "ana@x.com"})

    with pytest.raises(pydantic.ValidationError):
        await SqlUserRepository(db_session).get_by_email(Email("ana@x.com"))


async def test_add_leaves_created_at_and_updated_at_to_the_database(
    db_session: AsyncSession, users: UserRepository, ana: User
) -> None:
    await users.add(ana)

    # now() is the start time of the transaction, so the row holds it exactly.
    audit = await db_session.execute(
        text(
            "SELECT created_at = now(), updated_at = now() FROM auth_user"
            " WHERE id = :id"
        ),
        {"id": ana.id.root},
    )
    assert tuple(audit.one()) == (True, True)


async def test_a_query_span_keeps_the_statement_and_no_parameters(
    users: UserRepository, ana: User, spans: InMemorySpanExporter
) -> None:
    await users.add(ana)

    attributes = [dict(span.attributes or {}) for span in spans.get_finished_spans()]
    statements = [str(a["db.statement"]) for a in attributes if "db.statement" in a]
    assert any(s.startswith("INSERT INTO auth_user ") for s in statements)
    assert "fake$password" not in str(attributes)
    assert "ana@x.com" not in str(attributes)
