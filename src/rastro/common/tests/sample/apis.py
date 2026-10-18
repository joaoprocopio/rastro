from http import HTTPStatus

import pydantic
from django.http import HttpRequest, HttpResponse

from rastro.common.apis import parse_body, require_GET, require_POST, respond
from rastro.common.tests.sample.values import Color


class PaintInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    color: Color
    coats: int


class PaintOutput(pydantic.BaseModel):
    color: Color
    coats: int


@require_POST
def paint_api(request: HttpRequest) -> HttpResponse:
    input = parse_body(request, PaintInput)
    return respond(
        status=HTTPStatus.OK,
        output=PaintOutput(color=input.color, coats=input.coats),
    )


@require_GET
def paint_count_api(request: HttpRequest) -> HttpResponse:
    return respond(status=HTTPStatus.NO_CONTENT)


def boom_api(request: HttpRequest) -> HttpResponse:
    raise RuntimeError("boom")
