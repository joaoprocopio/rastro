from rastro import otel
from rastro.common.infrastructure.database import (
    create_database_engine,
    create_sessionmaker,
)
from rastro.settings import Settings
from rastro.task_app import create_task_app

# A missing variable stops the process here, and the error names it.
settings = Settings()

otel.instrument(settings=settings)

engine = create_database_engine(settings)
otel.instrument_engine(engine)

# The procrastinate command opens this App and runs its worker.
app = create_task_app(settings=settings, sessionmaker=create_sessionmaker(engine))
