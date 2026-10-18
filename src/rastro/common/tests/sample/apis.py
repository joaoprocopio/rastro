from http import HTTPStatus

import pydantic
from django.http import HttpRequest, HttpResponse

from rastro.common.apis import parse_body, respond
from rastro.common.tests.sample.values import Color


class PaintInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    color: Color
    coats: int


class PaintOutput(pydantic.BaseModel):
    color: Color
    coats: int


def paint_api(request: HttpRequest) -> HttpResponse:
    input = parse_body(request, PaintInput)
    return respond(
        status=HTTPStatus.OK,
        output=PaintOutput(color=input.color, coats=input.coats),
    )
