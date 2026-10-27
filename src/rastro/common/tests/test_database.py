from collections.abc import Awaitable, Callable

import httpx


async def test_a_request_that_succeeds_commits_its_writes(
    sample_client: httpx.AsyncClient, note_count: Callable[[], Awaitable[int]]
) -> None:
    await sample_client.post("/sample/notes")

    assert await note_count() == 1


async def test_a_request_that_raises_rolls_back_its_writes(
    sample_client: httpx.AsyncClient, note_count: Callable[[], Awaitable[int]]
) -> None:
    await sample_client.post("/sample/notes/rejected")

    assert await note_count() == 0


async def test_each_test_sees_no_row_of_another_test(
    sample_client: httpx.AsyncClient, note_count: Callable[[], Awaitable[int]]
) -> None:
    await sample_client.post("/sample/notes")
    await sample_client.post("/sample/notes")

    assert await note_count() == 2
