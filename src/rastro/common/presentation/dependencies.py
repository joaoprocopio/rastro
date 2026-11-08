from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from procrastinate import JobContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.settings import Settings


def app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


AppSettings = Annotated[Settings, Depends(app_settings)]


async def database_session(request: Request) -> AsyncIterator[AsyncSession]:
    sessionmaker: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with sessionmaker() as db_session, db_session.begin():
        yield db_session


DatabaseSession = Annotated[AsyncSession, Depends(database_session, scope="function")]


JOB_SESSIONMAKER_KEY = "sessionmaker"
JOB_SETTINGS_KEY = "settings"


def job_sessionmaker(context: JobContext) -> async_sessionmaker[AsyncSession]:
    sessionmaker = context.additional_context[JOB_SESSIONMAKER_KEY]
    # additional_context is an untyped dict, so the check gives mypy the type.
    if not isinstance(sessionmaker, async_sessionmaker):
        raise TypeError(f"The job context holds {sessionmaker!r} as its sessionmaker.")
    return sessionmaker


def job_settings(context: JobContext) -> Settings:
    settings: Settings = context.additional_context[JOB_SETTINGS_KEY]
    return settings
