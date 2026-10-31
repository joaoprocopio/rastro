import logging
from collections.abc import Awaitable, Callable

import pytest
from procrastinate import App

from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.presentation.tasks import (
    note_create_task,
    note_reject_task,
)

pytestmark = pytest.mark.usefixtures("sample_tables")


async def test_a_task_that_succeeds_commits_its_writes(
    task_app: App, note_count: Callable[[], Awaitable[int]]
) -> None:
    await note_create_task.defer_async()
    await task_app.run_worker_async()

    assert await note_count() == 1


async def test_a_task_that_raises_rolls_back_its_writes(
    task_app: App,
    note_count: Callable[[], Awaitable[int]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    await note_reject_task.defer_async()
    with caplog.at_level(logging.ERROR):
        await task_app.run_worker_async()

    # The worker logs the error of a failed job in place of raising it.
    (record,) = caplog.records
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], NoteRejectedError)
    assert await note_count() == 0
