from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes.user_attributes import USER_ID
from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import EmailInUseError
from rastro.auth.domain.value_objects import Email, SessionTokenHash
from rastro.auth.infrastructure.mappers import (
    session_from_row,
    session_to_row,
    user_from_row,
    user_to_row,
)
from rastro.auth.infrastructure.models import USER_EMAIL_KEY, SessionRow, UserRow
from rastro.common.infrastructure.repositories import existing_row, next_id


class SqlUserRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def next_id(self) -> int:
        return await next_id(self._db_session, UserRow)

    async def add(self, user: User) -> None:
        self._db_session.add(user_to_row(user))
        try:
            await self._db_session.flush()
        except IntegrityError as error:
            # A concurrent registration can insert the email after the use case's check.
            if (
                isinstance(error.orig, UniqueViolation)
                and error.orig.diag.constraint_name == USER_EMAIL_KEY
            ):
                raise EmailInUseError() from error
            raise

    async def update(self, user: User) -> None:
        # The load raises for a missing row, which merge alone would insert.
        await existing_row(self._db_session, UserRow, user.id)
        # merge copies only the columns that the mapper sets, so created_at stays.
        await self._db_session.merge(user_to_row(user))
        await self._db_session.flush()

    async def remove(self, user: User) -> None:
        await self._db_session.delete(
            await existing_row(self._db_session, UserRow, user.id)
        )
        await self._db_session.flush()

    async def get_by_id(self, id: int) -> User | None:
        row = await self._db_session.get(UserRow, id)
        return None if row is None else user_from_row(row)

    async def get_by_email(self, email: Email) -> User | None:
        row = await self._db_session.scalar(
            select(UserRow).where(UserRow.email == email.root)
        )
        return None if row is None else user_from_row(row)


class SqlSessionRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def next_id(self) -> int:
        return await next_id(self._db_session, SessionRow)

    async def add(self, session: Session) -> None:
        self._db_session.add(session_to_row(session))
        await self._db_session.flush()
        _trace_user(session)

    async def update(self, session: Session) -> None:
        await existing_row(self._db_session, SessionRow, session.id)
        await self._db_session.merge(session_to_row(session))
        await self._db_session.flush()
        _trace_user(session)

    async def remove(self, session: Session) -> None:
        await self._db_session.delete(
            await existing_row(self._db_session, SessionRow, session.id)
        )
        await self._db_session.flush()
        _trace_user(session)

    async def get_by_id(self, id: int) -> Session | None:
        row = await self._db_session.get(SessionRow, id)
        return None if row is None else _traced(session_from_row(row))

    async def get_by_token_hash(self, token_hash: SessionTokenHash) -> Session | None:
        row = await self._db_session.scalar(
            select(SessionRow).where(SessionRow.token_hash == token_hash.root)
        )
        return None if row is None else _traced(session_from_row(row))


def _trace_user(session: Session) -> None:
    # A span names the User of its Session by id, never by email.
    trace.get_current_span().set_attribute(USER_ID, session.user_id)


def _traced(session: Session) -> Session:
    _trace_user(session)
    return session
