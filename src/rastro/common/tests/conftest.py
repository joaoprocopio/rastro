from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.common.tests.sample.infrastructure.models import NoteRow


@pytest.fixture
def note_count(
    sessionmaker: async_sessionmaker[AsyncSession], sample_tables: None
) -> Callable[[], Awaitable[int]]:
    # A test reads the rows that a request or a task wrote, as the auth view tests do.
    async def count() -> int:
        async with sessionmaker() as db_session:
            count = await db_session.scalar(select(func.count()).select_from(NoteRow))
            if count is None:
                raise RuntimeError("COUNT returned no row.")
            return count

    return count
