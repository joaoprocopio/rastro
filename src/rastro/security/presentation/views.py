from http import HTTPStatus

from fastapi import APIRouter, Response

from rastro.common.presentation.dependencies import AppSettings
from rastro.common.presentation.problems import ErrorStatuses
from rastro.security.domain.errors import CsrfFailedError
from rastro.security.presentation.csrf_cookie import csrf_cookie_set

ERROR_STATUSES: ErrorStatuses = {
    CsrfFailedError: HTTPStatus.FORBIDDEN,
}

router = APIRouter()


@router.get("/csrf", status_code=HTTPStatus.NO_CONTENT)
async def csrf_set_view(response: Response, settings: AppSettings) -> None:
    csrf_cookie_set(response, settings=settings)
