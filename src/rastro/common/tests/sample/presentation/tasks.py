from procrastinate import Blueprint, JobContext

from rastro.common.presentation.dependencies import job_sessionmaker
from rastro.common.tests.sample.application.use_cases import note_create, note_reject
from rastro.common.tests.sample.presentation.dependencies import note_repository

blueprint = Blueprint()


@blueprint.task(pass_context=True)
async def note_create_task(context: JobContext) -> None:
    async with job_sessionmaker(context).begin() as db_session:
        await note_create(notes=note_repository(db_session))


@blueprint.task(pass_context=True)
async def note_paint_task(context: JobContext, *, color: str) -> None:
    pass


@blueprint.task(pass_context=True)
async def note_reject_task(context: JobContext) -> None:
    async with job_sessionmaker(context).begin() as db_session:
        await note_reject(notes=note_repository(db_session))
