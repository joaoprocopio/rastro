from datetime import datetime

from psycopg.errors import UniqueViolation
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.errors import EmailInUseError
from rastro.auth.domain.value_objects import (
    Email,
    HashedResetToken,
    HashedSessionToken,
)
from rastro.auth.infrastructure.mappers import (
    reset_token_from_row,
    reset_token_to_row,
    session_from_row,
    session_to_row,
    user_from_row,
    user_to_row,
)
from rastro.auth.infrastructure.models import (
    RESET_TOKEN_USER_KEY,
    USER_EMAIL_KEY,
    ResetTokenRow,
    SessionRow,
    UserRow,
)
from rastro.common.domain.value_objects import Id
from rastro.common.infrastructure.repositories import (
    existing_row,
    next_id,
    removed_count,
)


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

    async def remove_by_user_id(self, user_id: Id) -> None:
        await self._db_session.execute(
            delete(SessionRow).where(SessionRow.user_id == user_id.root)
        )

    async def remove_expired(self, *, at: datetime) -> int:
        return await removed_count(
            self._db_session,
            statement=delete(SessionRow).where(SessionRow.expires_at <= at),
        )

    async def get_by_hashed_token(
        self, hashed_token: HashedSessionToken
    ) -> Session | None:
        row = await self._db_session.scalar(
            select(SessionRow).where(SessionRow.hashed_token == hashed_token.root)
        )
        return None if row is None else session_from_row(row)


class SqlResetTokenRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def next_id(self) -> Id:
        return await next_id(self._db_session, column=ResetTokenRow.id)

    async def replace(self, reset_token: IssuedResetToken) -> None:
        row = reset_token_to_row(reset_token)
        statement = insert(ResetTokenRow).values(
            id=row.id,
            user_id=row.user_id,
            hashed_token=row.hashed_token,
            issued_at=row.issued_at,
            expires_at=row.expires_at,
        )
        # A concurrent writer holds the row, so this one waits and then overwrites it.
        await self._db_session.execute(
            statement.on_conflict_do_update(
                constraint=RESET_TOKEN_USER_KEY,
                set_={
                    "id": statement.excluded.id,
                    "hashed_token": statement.excluded.hashed_token,
                    "issued_at": statement.excluded.issued_at,
                    "expires_at": statement.excluded.expires_at,
                    "updated_at": func.now(),
                },
            )
        )

    async def get_by_user_id(self, user_id: Id) -> IssuedResetToken | None:
        row = await self._db_session.scalar(
            select(ResetTokenRow).where(ResetTokenRow.user_id == user_id.root)
        )
        return None if row is None else reset_token_from_row(row)

    async def consume(self, hashed_token: HashedResetToken) -> IssuedResetToken | None:
        # A concurrent consume waits for the row lock, and then its DELETE finds no row.
        row = await self._db_session.scalar(
            delete(ResetTokenRow)
            .where(ResetTokenRow.hashed_token == hashed_token.root)
            .returning(ResetTokenRow)
        )
        return None if row is None else reset_token_from_row(row)

    async def remove_expired(self, *, at: datetime) -> int:
        return await removed_count(
            self._db_session,
            statement=delete(ResetTokenRow).where(ResetTokenRow.expires_at <= at),
        )
