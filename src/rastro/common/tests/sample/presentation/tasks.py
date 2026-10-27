from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from taskiq import TaskiqDepends, async_shared_broker

from rastro.common.presentation.dependencies import task_sessionmaker
from rastro.common.tests.sample.application.use_cases import note_create, note_reject
from rastro.common.tests.sample.presentation.dependencies import note_repository


@async_shared_broker.task
async def note_create_task(
    sessionmaker: async_sessionmaker[AsyncSession] = TaskiqDepends(task_sessionmaker),
) -> None:
    async with sessionmaker.begin() as db_session:
        await note_create(notes=note_repository(db_session))


@async_shared_broker.task
async def note_reject_task(
    sessionmaker: async_sessionmaker[AsyncSession] = TaskiqDepends(task_sessionmaker),
) -> None:
    async with sessionmaker.begin() as db_session:
        await note_reject(notes=note_repository(db_session))
