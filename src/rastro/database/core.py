from collections.abc import Iterator
from functools import cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Session, sessionmaker

from rastro.config import get_settings

# Alembic reads constraint names from the metadata, so every constraint gets a
# deterministic name and a later migration can drop it by that name.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(MappedAsDataclass, DeclarativeBase):
    """Base for every SQLAlchemy model.

    `MappedAsDataclass` generates a typed `__init__`, so the type checker
    rejects a model built with a wrong or missing column value.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@cache
def get_engine() -> Engine:
    settings = get_settings()

    return create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout.total_seconds(),
        pool_recycle=int(settings.database_pool_recycle.total_seconds()),
        pool_pre_ping=True,
    )


@cache
def get_sessionmaker() -> sessionmaker[Session]:
    # `expire_on_commit=False` keeps loaded attributes readable after the
    # commit, so serializing the response does not issue a new SELECT.
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Yield one session per request, in one transaction.

    The transaction commits when the view returns and rolls back when it raises.
    """
    with get_sessionmaker().begin() as session:
        yield session


# `scope="function"` commits before FastAPI sends the response, so a failed
# commit reaches the client as an error in place of a lost write.
DbSession = Annotated[Session, Depends(get_db, scope="function")]
