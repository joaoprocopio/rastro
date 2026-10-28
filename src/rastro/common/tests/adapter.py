from collections.abc import Callable
from enum import StrEnum


class RepositoryKind(StrEnum):
    """The adapter that a repository behaviour test runs."""

    FAKE = "fake"
    SQL = "sql"

    def pick[F, S](self, *, fake: Callable[[], F], sql: Callable[[], S]) -> F | S:
        """Build only the chosen repository, so the fake case opens no database."""
        match self:
            case RepositoryKind.FAKE:
                return fake()
            case RepositoryKind.SQL:
                return sql()
