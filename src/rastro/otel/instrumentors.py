from typing import Any

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# The module opens with a file-level "type: ignore", so mypy sees it as empty.
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import AsyncEngine

_INSTRUMENTORS: tuple[tuple[type[BaseInstrumentor], dict[str, Any]], ...] = (
    (LoggingInstrumentor, {}),
)


def instrument_all() -> None:
    for instrumentor, options in _INSTRUMENTORS:
        instrumentor().instrument(**options)


def uninstrument_all() -> None:
    for instrumentor, _ in _INSTRUMENTORS:
        instrumentor().uninstrument()


# Each function below reads the global provider, so a process calls instrument first.
def instrument_app(app: FastAPI) -> None:
    # The ASGI send and receive spans double the rows of each request.
    FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])


def instrument_engine(engine: AsyncEngine) -> None:
    # 0.66b1 declares SQLAlchemy < 2.1 and instruments nothing without the skip.
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, skip_dep_check=True)
