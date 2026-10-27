from typing import Any

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncEngine

from rastro.common.infrastructure.models import Row


# The engine fixture runs env.py, which imports every models module.
def _differences(connection: Connection) -> list[Any]:
    context = MigrationContext.configure(connection)
    differences: list[Any] = compare_metadata(context, Row.metadata)
    return differences


async def test_the_migrations_create_every_table_of_the_models(
    engine: AsyncEngine,
) -> None:
    async with engine.connect() as connection:
        differences = await connection.run_sync(_differences)

    assert differences == []


async def test_the_ids_and_the_foreign_key_are_bigint(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        columns = (
            await connection.execute(
                text(
                    "SELECT table_name, column_name, data_type, is_identity"
                    " FROM information_schema.columns"
                    " WHERE (table_name, column_name) IN"
                    " (('auth_user', 'id'), ('auth_session', 'id'),"
                    " ('auth_session', 'user_id'))"
                    " ORDER BY table_name, column_name"
                )
            )
        ).all()

    assert [tuple(column) for column in columns] == [
        ("auth_session", "id", "bigint", "YES"),
        ("auth_session", "user_id", "bigint", "NO"),
        ("auth_user", "id", "bigint", "YES"),
    ]
