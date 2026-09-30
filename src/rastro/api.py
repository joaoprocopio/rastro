from http import HTTPStatus

from fastapi import APIRouter, Depends

from rastro.iam.views import router as iam_router
from rastro.problem import PROBLEM_MEDIA_TYPE, Problem
from rastro.security import verify_csrf

_PROBLEM_RESPONSE = {
    "content": {PROBLEM_MEDIA_TYPE: {"schema": Problem.model_json_schema()}}
}

# Every route under this router runs `verify_csrf`, so a new route is protected
# against CSRF without opting in.
api_router = APIRouter(
    dependencies=[Depends(verify_csrf)],
    responses={
        HTTPStatus.UNAUTHORIZED: _PROBLEM_RESPONSE,
        HTTPStatus.FORBIDDEN: _PROBLEM_RESPONSE,
        HTTPStatus.CONFLICT: _PROBLEM_RESPONSE,
        HTTPStatus.UNPROCESSABLE_ENTITY: _PROBLEM_RESPONSE,
    },
)

api_router.include_router(iam_router, prefix="/iam", tags=["iam"])
