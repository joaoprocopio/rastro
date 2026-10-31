from rastro import telemetry
from rastro.app import create_app
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

app = create_app(settings=settings, sessionmaker=create_sessionmaker(engine))
telemetry.instrument_app(app)
