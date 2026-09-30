import os

# The settings are read once and cached, so the test configuration goes into
# the environment before any `rastro` module loads. The database name is forced,
# so the suite never drops the database that `RASTRO_POSTGRES_DB` names for dev.
os.environ["RASTRO_POSTGRES_DB"] = "rastro_test"
os.environ["RASTRO_ALLOWED_HOSTS"] = "testserver"
os.environ["RASTRO_CSRF_TRUSTED_ORIGINS"] = "https://trusted.example"
os.environ.setdefault(
    "RASTRO_SECRET_KEY", "test-secret-key-with-at-least-32-characters"
)

from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from rastro.config import get_settings
from rastro.database.core import get_db, get_engine
from rastro.iam import service
from rastro.iam.models import Identity, IdentityRegister
from rastro.main import create_app

PYPROJECT = Path(__file__).parent / "pyproject.toml"
IDENTITY_PASSWORD = "password"  # noqa: S105


def _admin_engine() -> sa.Engine:
    url = get_settings().database_url.set(database="postgres")
    return sa.create_engine(url, isolation_level="AUTOCOMMIT", poolclass=sa.NullPool)


@pytest.fixture(scope="session")
def engine() -> Iterator[sa.Engine]:
    """Create the test database, and migrate it with Alembic."""
    database = get_settings().postgres_db
    admin = _admin_engine()

    with admin.connect() as connection:
        connection.execute(
            sa.text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
        )
        connection.execute(sa.text(f'CREATE DATABASE "{database}"'))

    engine = get_engine()
    with engine.begin() as connection:
        config = Config(toml_file=PYPROJECT, attributes={"connection": connection})
        command.upgrade(config, "head")

    yield engine

    engine.dispose()
    with admin.connect() as connection:
        connection.execute(sa.text(f'DROP DATABASE "{database}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def db_session(engine: sa.Engine) -> Iterator[Session]:
    """Yield a session whose writes vanish when the test ends.

    The outer transaction never commits. Each `commit()` inside the test only
    releases a savepoint, and the rollback at the end undoes all of them.
    """
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield session
        session.close()
        transaction.rollback()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """Yield an HTTPS client that already holds a CSRF cookie."""
    app = create_app(get_settings())

    def get_test_db() -> Iterator[Session]:
        try:
            yield db_session
            db_session.commit()
        except BaseException:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app, base_url="https://testserver") as client:
        client.get("/api/v1/iam/csrftoken")
        yield client


@pytest.fixture
def identity(db_session: Session) -> Identity:
    identity = service.create(
        db_session=db_session,
        identity_in=IdentityRegister(
            display_name="user",
            email="user@example.com",
            password=SecretStr(IDENTITY_PASSWORD),
        ),
    )
    db_session.commit()
    return identity
