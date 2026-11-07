import logging

from procrastinate import Blueprint, JobContext, RetryStrategy, builtin_tasks
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.application import use_cases
from rastro.auth.application.dtos import PasswordResetSendInput
from rastro.auth.domain.errors import EmailTemporaryError
from rastro.auth.domain.ports import PasswordResetJobs
from rastro.auth.domain.value_objects import Email
from rastro.auth.presentation import dependencies
from rastro.common.presentation.dependencies import (
    DatabaseSession,
    job_sessionmaker,
    job_settings,
)
from rastro.common.presentation.tasks import defer_in_transaction

PASSWORD_RESET_QUEUE = "password_reset"
PASSWORD_RESET_JOB_MAX_HOURS = 7 * 24

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


@blueprint.periodic(cron="0 * * * *")
@blueprint.task(pass_context=True)
async def reset_token_remove_expired_task(context: JobContext, timestamp: int) -> None:
    async with job_sessionmaker(context).begin() as db_session:
        output = await use_cases.reset_token_remove_expired(
            reset_tokens=dependencies.reset_token_repository(db_session),
            clock=dependencies.clock(),
        )
    logger.info("Expired Reset tokens removed: %d", output.count)


# This task takes an email address in place of an id, which spec #20 accepts, so the job row and the job logs hold the address.
@blueprint.task(
    pass_context=True,
    queue=PASSWORD_RESET_QUEUE,
    retry=RetryStrategy(
        exponential_wait=2, max_attempts=10, retry_exceptions=[EmailTemporaryError]
    ),
)
async def password_reset_send_task(context: JobContext, *, email: str) -> None:
    settings = job_settings(context)
    async with job_sessionmaker(context).begin() as db_session:
        output = await use_cases.password_reset_send(
            PasswordResetSendInput(email=Email.model_validate(email)),
            users=dependencies.user_repository(db_session),
            reset_tokens=dependencies.reset_token_repository(db_session),
            email_sender=dependencies.job_email_sender(context),
            clock=dependencies.clock(),
            lifetime=settings.reset_token_lifetime,
            cooldown=settings.reset_token_cooldown,
            token_bytes=settings.reset_token_bytes,
            link_url=settings.reset_link_url,
        )
    if output.no_answer:
        logger.warning(
            "The SMTP server gave no answer to the reset email of job %s, "
            "which may have gone out.",
            context.job.id,
        )


# A failed job holds an email address too, so this task removes it as well.
@blueprint.periodic(cron="0 0 * * *")
@blueprint.task(pass_context=True)
async def password_reset_remove_old_jobs_task(
    context: JobContext, timestamp: int
) -> None:
    await builtin_tasks.remove_old_jobs(
        context,
        max_hours=PASSWORD_RESET_JOB_MAX_HOURS,
        queue=PASSWORD_RESET_QUEUE,
        remove_failed=True,
    )


# It sits beside its task, because the infrastructure imports no presentation.
class ProcrastinatePasswordResetJobs:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def defer_send(self, email: Email) -> None:
        defer = defer_in_transaction(
            password_reset_send_task, db_session=self._db_session
        )
        await defer(email=email.root)


def password_reset_jobs(db_session: DatabaseSession) -> PasswordResetJobs:
    return ProcrastinatePasswordResetJobs(db_session)
