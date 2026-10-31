import logging

from procrastinate import Blueprint, JobContext

from rastro.auth.application import use_cases
from rastro.auth.presentation import dependencies
from rastro.common.presentation.dependencies import job_sessionmaker

logger = logging.getLogger(__name__)

blueprint = Blueprint()


@blueprint.periodic(cron="0 * * * *")
@blueprint.task(pass_context=True)
async def session_remove_expired_task(context: JobContext, timestamp: int) -> None:
    async with job_sessionmaker(context).begin() as db_session:
        output = await use_cases.session_remove_expired(
            sessions=dependencies.session_repository(db_session),
            clock=dependencies.clock(),
        )
    logger.info("Expired Sessions removed: %d", output.count)
