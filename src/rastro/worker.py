from rastro import otel
from rastro.auth.presentation.dependencies import email_sender
from rastro.common.infrastructure.database import (
    create_database_engine,
    create_sessionmaker,
)
from rastro.settings import Settings
from rastro.worker_app import create_worker_app

# A missing variable stops the process here, and the error names it.
settings = Settings()

otel.instrument(settings=settings)

engine = create_database_engine(settings)
otel.instrument_engine(engine)

# The procrastinate command opens this App and runs its worker.
app = create_worker_app(
    settings=settings,
    sessionmaker=create_sessionmaker(engine),
    email_sender=email_sender(settings),
)
