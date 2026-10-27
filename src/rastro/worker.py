from rastro import telemetry
from rastro.broker import create_broker
from rastro.common.infrastructure.database import (
    create_database_engine,
    create_sessionmaker,
)
from rastro.common.infrastructure.modules import import_every_app_module
from rastro.settings import Settings

# A missing variable stops the process here, and the error names it.
settings = Settings()

telemetry.instrument(settings=settings)

engine = create_database_engine(settings)
telemetry.instrument_engine(engine)

broker = create_broker(settings)
telemetry.instrument_broker(broker)
# task_sessionmaker reads it, as database_session reads app.state.sessionmaker.
broker.state.sessionmaker = create_sessionmaker(engine)

# The worker runs only the tasks that it imports.
import_every_app_module("presentation.tasks")
