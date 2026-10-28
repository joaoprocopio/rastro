from collections.abc import Callable
from enum import StrEnum


class Adapter(StrEnum):
    """The adapter that a repository behaviour test runs."""

    FAKE = "fake"
    SQL = "sql"

    def pick[F, S](self, *, fake: Callable[[], F], sql: Callable[[], S]) -> F | S:
        """Build only the chosen repository, so the fake case opens no database."""
        match self:
            case Adapter.FAKE:
                return fake()
            case Adapter.SQL:
                return sql()
