from rastro import telemetry
from rastro.app import create_app
from rastro.broker import create_broker
from rastro.common.infrastructure.database import (
    create_database_engine,
    create_sessionmaker,
)
from rastro.settings import Settings

# A missing or invalid variable stops the process here, and the error names it.
settings = Settings()

telemetry.instrument(settings=settings)

engine = create_database_engine(settings)
telemetry.instrument_engine(engine)

broker = create_broker(settings)
telemetry.instrument_broker(broker)

app = create_app(
    settings=settings, sessionmaker=create_sessionmaker(engine), broker=broker
)
telemetry.instrument_app(app)
