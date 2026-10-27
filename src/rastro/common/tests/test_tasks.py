from collections.abc import Awaitable, Callable

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.presentation.tasks import (
    note_create_task,
    note_reject_task,
)

pytestmark = pytest.mark.usefixtures("broker", "sample_tables")


async def test_a_task_that_succeeds_commits_its_writes(
    note_count: Callable[[], Awaitable[int]],
) -> None:
    await note_create_task.kiq()

    assert await note_count() == 1


async def test_a_task_that_raises_rolls_back_its_writes(
    note_count: Callable[[], Awaitable[int]],
) -> None:
    task = await note_reject_task.kiq()

    result = await task.wait_result()
    assert isinstance(result.error, NoteRejectedError)
    assert await note_count() == 0


async def test_a_task_produces_a_span_that_holds_its_queries(
    spans: InMemorySpanExporter,
) -> None:
    await note_create_task.kiq()

    finished = spans.get_finished_spans()
    (execute,) = [span for span in finished if span.kind == SpanKind.CONSUMER]
    assert execute.name == f"execute/{note_create_task.task_name}"
    (send,) = [span for span in finished if span.kind == SpanKind.PRODUCER]
    assert execute.context.trace_id == send.context.trace_id
    queries = [span for span in finished if span.kind == SpanKind.CLIENT]
    assert queries
    assert all(span.parent == execute.context for span in queries)
