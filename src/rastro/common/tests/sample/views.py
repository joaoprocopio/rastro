from http import HTTPStatus

from django.http import Http404, HttpRequest, HttpResponse

from rastro.common.tests.sample.models import Wall
from rastro.common.tests.sample.schemas import PaintApplyInput, PaintApplyOutput
from rastro.common.views import parse_body, require_GET, require_POST, respond


@require_POST
def paint_apply_view(request: HttpRequest) -> HttpResponse:
    body = parse_body(request, PaintApplyInput)
    output = PaintApplyOutput.model_validate(body)
    return respond(status=HTTPStatus.OK, output=output)


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
