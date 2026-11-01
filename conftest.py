import secrets
import uuid
from collections.abc import AsyncIterator, Callable
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
from procrastinate import App
from procrastinate.testing import InMemoryConnector
from pydantic import PostgresDsn, Secret
from sqlalchemy import Connection, NullPool, make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from rastro import telemetry
from rastro.app import ERROR_STATUSES, create_app
from rastro.auth.domain.ports import Clock, PasswordHasher
from rastro.auth.presentation import dependencies as auth_dependencies
from rastro.auth.tests.fakes import FakeClock, FakePasswordHasher
from rastro.common.presentation.problems import install_problem_handlers
from rastro.common.tests.adapter import RepositoryKind
from rastro.common.tests.sample.infrastructure.models import SampleRow
from rastro.common.tests.sample.presentation.tasks import (
    blueprint as sample_blueprint,
)
from rastro.common.tests.sample.presentation.views import (
    ERROR_STATUSES as SAMPLE_ERROR_STATUSES,
)
from rastro.common.tests.sample.presentation.views import router as sample_router
from rastro.settings import Settings
from rastro.task_app import create_task_app

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


def _alembic_config(connection: Connection) -> Config:
    # env.py runs on this connection, so the migrations run in the test database.
    config = Config(toml_file=ROOT / "pyproject.toml")
    config.attributes["connection"] = connection
    return config


def _migrate(connection: Connection) -> None:
    command.upgrade(_alembic_config(connection), "head")


@pytest.fixture
def alembic_config() -> Callable[[Connection], Config]:
    """Build the Alembic config whose env.py runs on the given connection."""
    return _alembic_config


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


@pytest.fixture(scope="session")
def unbound_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """The sessionmaker of `worker_app`, which `sessionmaker` binds to each test."""
    # Each request or task transaction becomes a savepoint in the test's transaction.
    return async_sessionmaker(
        join_transaction_mode="create_savepoint", expire_on_commit=False
    )


@pytest.fixture
def sessionmaker(
    unbound_sessionmaker: async_sessionmaker[AsyncSession], connection: AsyncConnection
) -> async_sessionmaker[AsyncSession]:
    unbound_sessionmaker.configure(bind=connection)
    return unbound_sessionmaker


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


@pytest.fixture(scope="session")
def worker_app(
    settings: Settings, unbound_sessionmaker: async_sessionmaker[AsyncSession]
) -> App:
    """The App that the worker builds, with the sample tasks added."""
    # add_tasks_from binds each task to its App, so the test run builds one App.
    app = create_task_app(settings=settings, sessionmaker=unbound_sessionmaker)
    app.add_tasks_from(sample_blueprint, namespace="sample")
    # A run defers no periodic job, so a test runs only the jobs that it defers.
    app.periodic_defaults["max_delay"] = -1
    # A run stops when no job is left, and the signal handlers stay with pytest.
    app.worker_defaults["wait"] = False
    app.worker_defaults["install_signal_handlers"] = False
    return app


@pytest.fixture
async def task_app(
    worker_app: App, sessionmaker: async_sessionmaker[AsyncSession]
) -> AsyncIterator[App]:
    """`worker_app` with no job, whose jobs run in the test's transaction."""
    with worker_app.replace_connector(InMemoryConnector()) as app:
        async with app.open_async():
            yield app


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
    password_hasher: PasswordHasher,
    clock: Clock,
) -> FastAPI:
    app = create_app(settings=settings, sessionmaker=sessionmaker)
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


@pytest.fixture
async def sample_tables(connection: AsyncConnection) -> None:
    # The tables live in the test's transaction, so they vanish with its rollback.
    await connection.run_sync(SampleRow.metadata.create_all)


@pytest.fixture
def sample_app(app: FastAPI, sample_tables: None) -> FastAPI:
    app.include_router(sample_router, prefix="/sample")
    install_problem_handlers(
        app, error_statuses={**ERROR_STATUSES, **SAMPLE_ERROR_STATUSES}
    )
    return app


@pytest.fixture
async def sample_client(
    sample_app: FastAPI, settings: Settings, csrf_token: str
) -> AsyncIterator[httpx.AsyncClient]:
    # The 500 handler sends its response and then raises the exception again.
    transport = httpx.ASGITransport(app=sample_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://testserver",
        cookies={settings.csrf_cookie_name: csrf_token},
        headers={settings.csrf_header_name: csrf_token},
    ) as client:
        yield client
