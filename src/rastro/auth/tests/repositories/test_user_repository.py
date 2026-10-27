from datetime import UTC, datetime

import pydantic
import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.auth.domain.aggregates import User
from rastro.auth.domain.errors import EmailInUseError
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


async def test_get_by_id_and_get_by_email_read_back_every_field_that_add_wrote(
    db_session: AsyncSession, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    users = SqlUserRepository(db_session)
    ada = await _ada(users)

    await users.add(ada)

    # A second session reads the row from the database, not from the first's cache.
    async with sessionmaker() as reader:
        assert await SqlUserRepository(reader).get_by_id(ada.id) == ada
        assert await SqlUserRepository(reader).get_by_email(ada.email) == ada


async def test_get_by_id_and_get_by_email_answer_none_for_an_unknown_user(
    db_session: AsyncSession,
) -> None:
    users = SqlUserRepository(db_session)

    assert await users.get_by_id(Id(1)) is None
    assert await users.get_by_email(Email("nobody@x.com")) is None


async def test_two_next_id_calls_return_two_different_ids(
    db_session: AsyncSession,
) -> None:
    users = SqlUserRepository(db_session)

    first, second = await users.next_id(), await users.next_id()

    assert isinstance(first, Id)
    assert first != second


async def test_a_second_add_with_the_same_email_raises_email_in_use(
    db_session: AsyncSession,
) -> None:
    users = SqlUserRepository(db_session)
    await users.add(await _ada(users))
    other = User(
        id=await users.next_id(),
        email=Email("ada@x.com"),
        display_name=DisplayName("Other"),
        hashed_password=HashedPassword("fake$other"),
    )

    with pytest.raises(EmailInUseError):
        await users.add(other)


async def test_update_writes_every_field_of_the_user(
    db_session: AsyncSession, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    users = SqlUserRepository(db_session)
    ada = await _ada(users)
    await users.add(ada)
    ada.email = Email("ada@y.com")
    ada.display_name = DisplayName("Ada L.")
    ada.hashed_password = HashedPassword("fake$rehashed")

    await users.update(ada)

    async with sessionmaker() as reader:
        assert await SqlUserRepository(reader).get_by_id(ada.id) == ada


async def test_update_of_a_user_with_no_row_raises_lookup_error_and_adds_no_row(
    db_session: AsyncSession, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    users = SqlUserRepository(db_session)
    ada = await _ada(users)

    with pytest.raises(LookupError):
        await users.update(ada)

    async with sessionmaker() as reader:
        assert await SqlUserRepository(reader).get_by_id(ada.id) is None


async def test_remove_deletes_the_user(
    db_session: AsyncSession, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    users = SqlUserRepository(db_session)
    ada = await _ada(users)
    await users.add(ada)

    await users.remove(ada)

    async with sessionmaker() as reader:
        assert await SqlUserRepository(reader).get_by_id(ada.id) is None


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
