import pytest
from procrastinate import App
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.common.tests.sample.infrastructure.models import NoteRow
from rastro.common.tests.sample.presentation.tasks import note_create_task


@pytest.mark.usefixtures("sample_tables")
async def test_a_job_writes_through_the_sessionmaker_that_create_worker_app_receives(
    worker_app: App, reader: AsyncSession
) -> None:
    await note_create_task.defer_async()
    await worker_app.run_worker_async()

    assert await reader.scalar(select(func.count()).select_from(NoteRow)) == 1
