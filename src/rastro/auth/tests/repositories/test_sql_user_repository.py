import asyncio

import pydantic
import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.auth.application.dtos import PasswordResetConfirmInput, SessionStartInput
from rastro.auth.application.use_cases import password_reset_confirm, session_start
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import IncorrectCredentialsError
from rastro.auth.domain.ports import PasswordHasher, UserRepository
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    RawPassword,
    SessionToken,
)
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.tests.conftest import until_a_statement_waits
from rastro.auth.tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    PausingUserRepository,
)
from rastro.auth.tests.repositories.conftest import COMMITTED_TOKEN, LIFETIME, START
from rastro.common.domain.value_objects import Id, TokenBytes
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.common.tests.adapter import RepositoryKind

INSERT_USER = text(
    "INSERT INTO auth_user"
    " (id, email, display_name, hashed_password, created_at, updated_at)"
    " VALUES (:id, :email, 'Ana', 'fake$x', now(), now())"
)
CREDENTIALS = SessionStartInput(
    email=Email("committed@x.com"), password=RawPassword(SecretStr("password"))
)
CONFIRMATION = PasswordResetConfirmInput(
    token=COMMITTED_TOKEN, password=RawPassword(SecretStr("newpassword"))
)
NEW_HASH = HashedPassword("fake$newpassword")
TOKEN_BYTES = TokenBytes(16)
EACH_KIND_OF_HASH = pytest.mark.parametrize(
    "raced_user",
    ["fake$password", "outdated$password"],
    ids=["current_hash", "outdated_hash"],
    indirect=True,
)
LOCKED_READ = "SELECT %FROM auth_user%FOR %"
UPDATE_OF_THE_USER = "UPDATE auth_user%"


@pytest.fixture
def adapter() -> RepositoryKind:
    """The tests of this module run only on Postgres."""
    return RepositoryKind.SQL


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
    statements = [str(a["db.query.text"]) for a in attributes if "db.query.text" in a]
    assert any(s.startswith("INSERT INTO auth_user ") for s in statements)
    assert "fake$password" not in str(attributes)
    assert "ana@x.com" not in str(attributes)


@EACH_KIND_OF_HASH
async def test_a_confirmation_that_runs_second_removes_the_new_session_and_keeps_its_hash(
    engine: AsyncEngine,
    raced_user: User,
    password_hasher: PasswordHasher,
    clock: FakeClock,
) -> None:
    sessionmaker = create_sessionmaker(engine)

    # The TaskGroup cancels each task when the test fails, so its statement stops waiting.
    async with (
        sessionmaker() as signing_in,
        sessionmaker() as confirming,
        sessionmaker() as probe,
        asyncio.TaskGroup() as tasks,
    ):
        users = PausingUserRepository(SqlUserRepository(signing_in))
        sign_in = tasks.create_task(
            session_start(
                CREDENTIALS,
                users=users,
                sessions=SqlSessionRepository(signing_in),
                password_hasher=password_hasher,
                clock=clock,
                lifetime=LIFETIME,
                token_bytes=TOKEN_BYTES,
            )
        )
        async with asyncio.timeout(5):
            await users.read.wait()
        confirmation = tasks.create_task(
            password_reset_confirm(
                CONFIRMATION,
                users=SqlUserRepository(confirming),
                sessions=SqlSessionRepository(confirming),
                reset_tokens=SqlResetTokenRepository(confirming),
                password_hasher=password_hasher,
                clock=clock,
            )
        )
        await until_a_statement_waits(probe, statement=UPDATE_OF_THE_USER)
        users.resume.set()
        output = await sign_in
        await signing_in.commit()
        await confirmation
        await confirming.commit()

    async with sessionmaker() as reader:
        stored = await SqlUserRepository(reader).get_by_id(raced_user.id)
        new_session = await SqlSessionRepository(reader).get_by_hashed_token(
            output.token.digest()
        )
    assert stored is not None
    assert stored.hashed_password == NEW_HASH
    assert new_session is None


@EACH_KIND_OF_HASH
async def test_a_confirmation_that_runs_first_makes_the_old_password_fail(
    engine: AsyncEngine,
    raced_user: User,
    password_hasher: PasswordHasher,
    clock: FakeClock,
) -> None:
    sessionmaker = create_sessionmaker(engine)

    async with (
        sessionmaker() as confirming,
        sessionmaker() as signing_in,
        sessionmaker() as probe,
    ):
        await password_reset_confirm(
            CONFIRMATION,
            users=SqlUserRepository(confirming),
            sessions=SqlSessionRepository(confirming),
            reset_tokens=SqlResetTokenRepository(confirming),
            password_hasher=password_hasher,
            clock=clock,
        )
        with pytest.RaisesGroup(IncorrectCredentialsError):
            async with asyncio.TaskGroup() as tasks:
                tasks.create_task(
                    session_start(
                        CREDENTIALS,
                        users=SqlUserRepository(signing_in),
                        sessions=SqlSessionRepository(signing_in),
                        password_hasher=password_hasher,
                        clock=clock,
                        lifetime=LIFETIME,
                        token_bytes=TOKEN_BYTES,
                    )
                )
                await until_a_statement_waits(probe, statement=LOCKED_READ)
                await confirming.commit()

    async with sessionmaker() as reader:
        stored = await SqlUserRepository(reader).get_by_id(raced_user.id)
    assert stored is not None
    assert stored.hashed_password == NEW_HASH


async def test_a_second_sign_in_waits_for_the_first_and_reads_its_new_hash(
    engine: AsyncEngine,
    committed_user: User,
    password_hasher: FakePasswordHasher,
    clock: FakeClock,
) -> None:
    sessionmaker = create_sessionmaker(engine)
    committed_user.hashed_password = HashedPassword("outdated$password")
    async with sessionmaker.begin() as db_session:
        await SqlUserRepository(db_session).update(committed_user)

    async with (
        sessionmaker() as first,
        sessionmaker() as second,
        sessionmaker() as probe,
        asyncio.TaskGroup() as tasks,
    ):
        users = PausingUserRepository(SqlUserRepository(first))
        first_sign_in = tasks.create_task(
            session_start(
                CREDENTIALS,
                users=users,
                sessions=SqlSessionRepository(first),
                password_hasher=password_hasher,
                clock=clock,
                lifetime=LIFETIME,
                token_bytes=TOKEN_BYTES,
            )
        )
        async with asyncio.timeout(5):
            await users.read.wait()
        second_sign_in = tasks.create_task(
            session_start(
                CREDENTIALS,
                users=SqlUserRepository(second),
                sessions=SqlSessionRepository(second),
                password_hasher=password_hasher,
                clock=clock,
                lifetime=LIFETIME,
                token_bytes=TOKEN_BYTES,
            )
        )
        await until_a_statement_waits(probe, statement=LOCKED_READ)
        users.resume.set()
        await first_sign_in
        await first.commit()
        await second_sign_in
        await second.commit()

    assert password_hasher.hashed == [CREDENTIALS.password]


async def test_a_locked_read_leaves_the_foreign_key_check_of_a_new_session_free(
    engine: AsyncEngine, committed_user: User
) -> None:
    sessionmaker = create_sessionmaker(engine)

    async with sessionmaker() as locking, sessionmaker() as adding:
        await SqlUserRepository(locking).get_by_email_locked(committed_user.email)
        sessions = SqlSessionRepository(adding)
        session = Session.start(
            id=await sessions.next_id(),
            user_id=committed_user.id,
            token=SessionToken(SecretStr("added")),
            at=START,
            lifetime=LIFETIME,
        )

        async with asyncio.timeout(5):
            await sessions.add(session)
