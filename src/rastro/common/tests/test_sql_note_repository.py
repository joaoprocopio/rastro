import pydantic
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.common.domain.value_objects import Id
from rastro.common.tests.sample.infrastructure.models import NoteRow
from rastro.common.tests.sample.infrastructure.repositories import SqlNoteRepository

pytestmark = pytest.mark.usefixtures("sample_tables")


async def test_a_row_that_breaks_its_value_object_fails_to_become_an_aggregate(
    db_session: AsyncSession,
) -> None:
    db_session.add(NoteRow(id=1, color="Green"))
    await db_session.flush()

    with pytest.raises(pydantic.ValidationError):
        await SqlNoteRepository(db_session).get_by_id(Id(1))
