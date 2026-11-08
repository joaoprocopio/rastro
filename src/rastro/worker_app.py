from procrastinate import App, Blueprint, PsycopgConnector
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.auth.domain.ports import EmailSender
from rastro.auth.presentation.dependencies import JOB_EMAIL_SENDER_KEY
from rastro.common.infrastructure.modules import import_every_app_module
from rastro.common.presentation.dependencies import (
    JOB_SESSIONMAKER_KEY,
    JOB_SETTINGS_KEY,
)
from rastro.settings import Settings


def _conninfo(settings: Settings) -> str:
    # libpq reads the URL of the setting once the scheme names no SQLAlchemy driver.
    url = str(settings.postgres_url.get_secret_value())
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


# add_tasks_from binds each task of a blueprint to this App, so a process calls it once.
def create_job_app(*, settings: Settings) -> App:
    # A view defers on the connection of its transaction, so the API never opens the pool.
    app = App(connector=PsycopgConnector(conninfo=_conninfo(settings)))
    for label, module in import_every_app_module("presentation.tasks").items():
        blueprint = module.blueprint
        if not isinstance(blueprint, Blueprint):
            raise TypeError(f"{module.__name__}.blueprint is not a Blueprint.")
        app.add_tasks_from(blueprint, namespace=label)
    return app


def create_worker_app(
    *,
    settings: Settings,
    sessionmaker: async_sessionmaker[AsyncSession],
    email_sender: EmailSender,
) -> App:
    app = create_job_app(settings=settings)
    app.worker_defaults["additional_context"] = {
        JOB_SESSIONMAKER_KEY: sessionmaker,
        JOB_SETTINGS_KEY: settings,
        JOB_EMAIL_SENDER_KEY: email_sender,
    }
    return app
