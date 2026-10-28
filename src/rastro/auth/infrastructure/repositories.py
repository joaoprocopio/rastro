from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import EmailInUseError
from rastro.auth.domain.value_objects import Email, HashedSessionToken
from rastro.auth.infrastructure.mappers import (
    session_from_row,
    session_to_row,
    user_from_row,
    user_to_row,
)
from rastro.auth.infrastructure.models import USER_EMAIL_KEY, SessionRow, UserRow
from rastro.common.domain.value_objects import Id
from rastro.common.infrastructure.repositories import existing_row, next_id


class SqlUserRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def next_id(self) -> Id:
        return await next_id(self._db_session, column=UserRow.id)

    async def add(self, user: User) -> None:
        self._db_session.add(user_to_row(user))
        await self._flush()

    async def update(self, user: User) -> None:
        # The load raises for a missing row, which merge alone would insert.
        await existing_row(self._db_session, UserRow, user.id)
        # merge copies only the columns that the mapper sets, so created_at stays.
        await self._db_session.merge(user_to_row(user))
        await self._flush()

    async def get_by_id(self, id: Id) -> User | None:
        row = await self._db_session.get(UserRow, id.root)
        return None if row is None else user_from_row(row)

    async def get_by_email(self, email: Email) -> User | None:
        row = await self._db_session.scalar(
            select(UserRow).where(UserRow.email == email.root)
        )
        return None if row is None else user_from_row(row)

    async def _flush(self) -> None:
        try:
            await self._db_session.flush()
        except IntegrityError as error:
            # A concurrent write can take the email after the use case's check.
            if (
                isinstance(error.orig, UniqueViolation)
                and error.orig.diag.constraint_name == USER_EMAIL_KEY
            ):
                raise EmailInUseError() from error
            raise


class SqlSessionRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def next_id(self) -> Id:
        return await next_id(self._db_session, column=SessionRow.id)

    async def add(self, session: Session) -> None:
        self._db_session.add(session_to_row(session))
        await self._db_session.flush()

    async def remove(self, session: Session) -> None:
        await self._db_session.delete(
            await existing_row(self._db_session, SessionRow, session.id)
        )
        await self._db_session.flush()

    async def get_by_hashed_token(
        self, hashed_token: HashedSessionToken
    ) -> Session | None:
        row = await self._db_session.scalar(
            select(SessionRow).where(SessionRow.hashed_token == hashed_token.root)
        )
        return None if row is None else session_from_row(row)
