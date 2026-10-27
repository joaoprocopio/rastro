from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from rastro.common.infrastructure.models import Row
from tests.architecture.rules import mapped_tables, table_violations

SAMPLE_MODULE = "rastro.paint.models"


def test_every_row_subclasses_row_and_starts_with_its_app_label() -> None:
    assert table_violations(mapped_tables()) == []


def test_the_check_finds_the_rows_of_the_apps() -> None:
    names = [f"{table.__module__}.{table.__qualname__}" for table in mapped_tables()]

    assert "rastro.auth.infrastructure.models.UserRow" in names
    assert "rastro.common.tests.sample.infrastructure.models.NoteRow" in names


def test_the_check_reports_a_row_that_skips_row() -> None:
    class Base(DeclarativeBase):
        pass

    class Ceiling(Base):
        __tablename__ = "paint_ceiling"
        __module__ = SAMPLE_MODULE

        id: Mapped[int] = mapped_column(primary_key=True)

    row = "rastro.common.infrastructure.models.Row"
    assert table_violations([Ceiling]) == [
        f"rastro.paint.models.Ceiling: does not subclass {row}"
    ]


def test_the_check_reports_a_table_name_without_its_app_label() -> None:
    # An abstract row stays out of the registry that the first test reads.
    class Brush(Row):
        __abstract__ = True
        __tablename__ = "brush"
        __module__ = SAMPLE_MODULE

    assert table_violations([Brush]) == [
        "rastro.paint.models.Brush: table name 'brush' does not start with 'paint_'"
    ]
