import asyncio

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

from rastro.common.infrastructure.models import Row
from rastro.common.infrastructure.modules import import_every_app_module
from rastro.settings import Settings


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Row.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_on_a_new_engine() -> None:
    settings = Settings()
    engine = create_async_engine(
        str(settings.postgres_url.get_secret_value()), poolclass=pool.NullPool
    )
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


# Autogenerate drops the table of any models module that it does not import.
import_every_app_module("infrastructure.models")

# The test suite passes its own connection, so the migrations run in its database.
connection = context.config.attributes.get("connection")
if connection is None:
    asyncio.run(_run_on_a_new_engine())
else:
    _run(connection)
