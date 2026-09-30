"""The metadata of every model, for Alembic and the tests.

A model module missing from the imports below is invisible to
`alembic revision --autogenerate`, which then emits a migration that drops the
model's table.
"""

from typing import Final

from rastro.database.core import Base
from rastro.iam import models as iam_models
from rastro.iam.session import models as iam_session_models

MODEL_MODULES: Final = (iam_models, iam_session_models)

target_metadata = Base.metadata
