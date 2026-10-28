from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends

from rastro.common.presentation.problems import ErrorStatuses
from rastro.common.tests.sample.application import use_cases
from rastro.common.tests.sample.application.dtos import PaintApplyInput
from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.domain.ports import NoteRepository
from rastro.common.tests.sample.presentation.dependencies import note_repository

ERROR_STATUSES: ErrorStatuses = {
    NoteRejectedError: HTTPStatus.CONFLICT,
}

router = APIRouter()


@router.post("/notes", status_code=HTTPStatus.NO_CONTENT)
async def note_create_view(
    notes: Annotated[NoteRepository, Depends(note_repository)],
) -> None:
    await use_cases.note_create(notes=notes)


@router.post("/notes/rejected", status_code=HTTPStatus.NO_CONTENT)
async def note_reject_view(
    notes: Annotated[NoteRepository, Depends(note_repository)],
) -> None:
    await use_cases.note_reject(notes=notes)


@router.post("/paints", status_code=HTTPStatus.NO_CONTENT)
async def paint_apply_view(body: PaintApplyInput) -> None:
    pass


@router.get("/boom")
async def boom_raise_view() -> None:
    raise RuntimeError("boom")


@router.api_route(
    "/csrf",
    methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    status_code=HTTPStatus.NO_CONTENT,
)
async def csrf_pass_view() -> None:
    pass
