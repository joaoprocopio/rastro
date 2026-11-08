from rastro import otel
from rastro.api_app import create_api_app
from rastro.common.infrastructure.database import (
    create_database_engine,
    create_sessionmaker,
)
from rastro.settings import Settings
from rastro.worker_app import create_job_app

# A missing or invalid variable stops the process here, and the error names it.
settings = Settings()

otel.instrument(settings=settings)

engine = create_database_engine(settings)
otel.instrument_engine(engine)

# A view defers a job through its task, which raises until an App binds it.
create_job_app(settings=settings)

app = create_api_app(settings=settings, sessionmaker=create_sessionmaker(engine))
otel.instrument_app(app)
