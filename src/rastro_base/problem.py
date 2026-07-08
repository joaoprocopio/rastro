import json
from collections.abc import Mapping
from http import HTTPStatus
from typing import Optional

import pydantic

from rastro.codes import ErrorCode
from rastro_base.error import BaseError
from rastro_base.mapper import Mapper
from rastro_base.pydantic import BaseModel

# RFC 7807 members that must never be overwritten by a spread extension.
# `type` and `instance` are reserved by the spec even though we don't emit them.
RESERVED_MEMBERS = frozenset({"type", "status", "title", "detail", "instance", "code"})


class Problem(BaseModel):
    """An RFC 7807 problem details object."""

    model_config = pydantic.ConfigDict(frozen=True)

    code: str
    title: str
    status: int
    detail: Optional[str] = None
    extensions: Optional[Mapping[str, object]] = None

    @pydantic.model_serializer
    def _serialize(self) -> dict[str, object]:
        problem: dict[str, object] = {
            "code": self.code,
            "status": self.status,
            "title": self.title,
        }

        if self.detail is not None:
            problem["detail"] = self.detail

        if self.extensions is not None:
            for key, value in self.extensions.items():
                if key in RESERVED_MEMBERS:
                    continue
                problem[key] = value

        return problem


class ProblemMapper(Mapper[BaseError, Problem]):
    @staticmethod
    def map(source: BaseError) -> Problem:
        return Problem(
            code=source.code,
            status=source.status,
            title=source.title,
            detail=source.detail,
            extensions=source.extensions,
        )


class RequestValidationError(BaseError):
    code = ErrorCode.BASE_VALIDATION_ERROR
    status = HTTPStatus.UNPROCESSABLE_ENTITY
    title = "Validation Error"


class ValidationErrorMapper(Mapper[pydantic.ValidationError, Problem]):
    @staticmethod
    def map(source: pydantic.ValidationError) -> Problem:
        # `.json()` coerces non-JSON-safe error fields (e.g. a raw `bytes`
        # request body echoed back as `input`, or a `ValueError` in `ctx`)
        # into string forms, so the response can't blow up in `JsonResponse`.
        errors: object = json.loads(source.json(include_url=False))

        return ProblemMapper.map(
            RequestValidationError(
                detail="The request payload failed validation.",
                extensions={"errors": errors},
            )
        )
