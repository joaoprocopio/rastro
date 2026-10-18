from http import HTTPStatus

import pydantic
from django.http import Http404, HttpRequest, HttpResponse

from rastro.common.tests.sample.models import Wall
from rastro.common.tests.sample.values import Color
from rastro.common.views import parse_body, require_GET, require_POST, respond


class PaintInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    color: Color
    coats: int


class PaintOutput(pydantic.BaseModel):
    color: Color
    coats: int


@require_POST
def paint_apply_view(request: HttpRequest) -> HttpResponse:
    input = parse_body(request, PaintInput)
    return respond(
        status=HTTPStatus.OK,
        output=PaintOutput(color=input.color, coats=input.coats),
    )


@require_GET
def paint_count_view(request: HttpRequest) -> HttpResponse:
    return respond(status=HTTPStatus.NO_CONTENT)


def boom_raise_view(request: HttpRequest) -> HttpResponse:
    raise RuntimeError("boom")


@require_GET
def paint_find_view(request: HttpRequest) -> HttpResponse:
    raise Http404


@require_POST
def wall_paint_view(request: HttpRequest) -> HttpResponse:
    Wall.objects.create(coats=-1)
    return respond(status=HTTPStatus.NO_CONTENT)
