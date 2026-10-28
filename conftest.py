import secrets
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pydantic import PostgresDsn, Secret
from sqlalchemy import Connection, NullPool, make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from taskiq import InMemoryBroker, async_shared_broker

from rastro import telemetry
from rastro.app import create_app
from rastro.auth.domain.ports import Clock, PasswordHasher
from rastro.auth.presentation import dependencies as auth_dependencies
from rastro.auth.tests.fakes import FakeClock, FakePasswordHasher
from rastro.common.tests.adapter import RepositoryKind
from rastro.settings import Settings

ROOT = Path(__file__).parent


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def settings() -> Settings:
    # A variable in the environment overrides the local value of .env.example.
    local = Settings(_env_file=ROOT / ".env.example")
    # Each run owns its database, so parallel runs can share one Postgres server.
    url = make_url(str(local.postgres_url.get_secret_value())).set(
        database=f"rastro_test_{uuid.uuid4().hex}"
    )
    # str() of a URL masks the password, so the copy renders it in full.
    postgres_url = Secret(PostgresDsn(url.render_as_string(hide_password=False)))
    return local.model_copy(update={"postgres_url": postgres_url})


@pytest.fixture(scope="session")
def span_exporter() -> InMemorySpanExporter:
    # The instrumentations read the global provider, which a process sets only once.
    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)
    return exporter


@pytest.fixture
def spans(span_exporter: InMemorySpanExporter) -> InMemorySpanExporter:
    span_exporter.clear()
    return span_exporter


def _migrate(connection: Connection) -> None:
    config = Config(toml_file=ROOT / "pyproject.toml")
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    url = make_url(str(settings.postgres_url.get_secret_value()))
    server = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    async with server.connect() as connection:
        await connection.execute(text(f'CREATE DATABASE "{url.database}"'))

    engine = create_async_engine(url, poolclass=NullPool)
    telemetry.instrument_engine(engine)
    async with engine.begin() as connection:
        await connection.run_sync(_migrate)

    yield engine

    await engine.dispose()
    async with server.connect() as connection:
        await connection.execute(text(f'DROP DATABASE "{url.database}" WITH (FORCE)'))
    await server.dispose()


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    # The test's writes, commits included, live in this transaction, which rolls back.
    async with engine.connect() as connection:
        transaction = await connection.begin()
        yield connection
        await transaction.rollback()


@pytest.fixture
def sessionmaker(connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    # Each request or task transaction becomes a savepoint in the test's transaction.
    return async_sessionmaker(
        connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )


@pytest.fixture
async def db_session(connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """A database session whose commit or rollback is a savepoint, as in a request."""
    async with AsyncSession(
        connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    ) as db_session:
        yield db_session


@pytest.fixture
async def reader(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """A second database session, whose reads skip the identity map of `db_session`."""
    async with sessionmaker() as reader:
        yield reader


@pytest.fixture(params=list(RepositoryKind))
def adapter(request: pytest.FixtureRequest) -> RepositoryKind:
    """The adapter of a repository behaviour test, and only `SQL` opens the database."""
    return RepositoryKind(request.param)


@pytest.fixture
async def broker(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[InMemoryBroker]:
    # A task runs to its end inside kiq, and its error reaches the test.
    broker = InMemoryBroker(await_inplace=True)
    broker.state.sessionmaker = sessionmaker
    telemetry.instrument_broker(broker)
    async_shared_broker.default_broker(broker)
    async with broker:
        yield broker


@pytest.fixture
def password_hasher() -> PasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 1, 1, tzinfo=UTC))


@pytest.fixture
def app(
    settings: Settings,
    sessionmaker: async_sessionmaker[AsyncSession],
    broker: InMemoryBroker,
    password_hasher: PasswordHasher,
    clock: Clock,
) -> FastAPI:
    app = create_app(settings=settings, sessionmaker=sessionmaker, broker=broker)
    telemetry.instrument_app(app)
    # Each process-wide adapter gets a fake, so no test runs a real one by accident.
    app.dependency_overrides[auth_dependencies.password_hasher] = lambda: (
        password_hasher
    )
    app.dependency_overrides[auth_dependencies.clock] = lambda: clock
    return app


@pytest.fixture
def csrf_token() -> str:
    return secrets.token_urlsafe()


@pytest.fixture
async def client(
    app: FastAPI, settings: Settings, csrf_token: str
) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://testserver",
        cookies={settings.csrf_cookie_name: csrf_token},
        headers={settings.csrf_header_name: csrf_token},
    ) as client:
        yield client
