import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from rastro.database.metadata import target_metadata


def test_migrations_match_the_models(engine: sa.Engine) -> None:
    """Fail when a model changes without an Alembic revision to match it."""
    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection, opts={"compare_server_default": True}
        )
        diff: object = compare_metadata(context, target_metadata)

    assert diff == []
