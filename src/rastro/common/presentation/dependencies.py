from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from taskiq import TaskiqDepends, TaskiqState


async def database_session(request: Request) -> AsyncIterator[AsyncSession]:
    sessionmaker: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with sessionmaker() as db_session, db_session.begin():
        yield db_session


DatabaseSession = Annotated[AsyncSession, Depends(database_session, scope="function")]


def task_sessionmaker(
    state: TaskiqState = TaskiqDepends(),
) -> async_sessionmaker[AsyncSession]:
    sessionmaker: async_sessionmaker[AsyncSession] = state.sessionmaker
    return sessionmaker
