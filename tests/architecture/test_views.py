from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, URLResolver, get_resolver, include, path
from django.urls.utils import get_callable

from tests.architecture.helpers import module_with
from tests.architecture.rules import url_violations, view_violations

SAMPLE_VIEWS = "rastro.sample.views"


def test_every_rastro_url_has_a_name_in_a_namespace_and_routes_to_a_view() -> None:
    assert url_violations(get_resolver().url_patterns) == []


def test_every_error_handler_is_a_view() -> None:
    resolver = get_resolver()
    handlers = [
        resolver.resolve_error_handler(404),
        resolver.resolve_error_handler(500),
        get_callable(settings.CSRF_FAILURE_VIEW),
    ]

    assert [
        violation for handler in handlers for violation in view_violations(handler)
    ] == []


def _sample_patterns() -> list[URLPattern | URLResolver]:
    def wall_paint_view(request: HttpRequest) -> HttpResponse:
        return HttpResponse()

    def wall_paint_api(request: HttpRequest) -> HttpResponse:
        return HttpResponse()

    module_with(SAMPLE_VIEWS, wall_paint_view, wall_paint_api)
    return [
        path("named", include(([path("", wall_paint_view, name="paint")], "sample"))),
        path("unnamed", include(([path("", wall_paint_view)], "sample"))),
        path("outside", wall_paint_view, name="paint"),
        path("api", include(([path("", wall_paint_api, name="paint")], "sample"))),
    ]


def test_the_check_reports_each_url_and_view_that_breaks_a_rule() -> None:
    assert url_violations(_sample_patterns()) == [
        "rastro.sample.views.wall_paint_view: URL has no name",
        "rastro.sample.views.wall_paint_view: URL is outside an app namespace",
        "rastro.sample.views.wall_paint_api: name does not follow <entity>_<action>_view",
    ]


def test_the_check_reports_a_view_outside_a_views_module() -> None:
    def wall_paint_view(request: HttpRequest) -> HttpResponse:
        return HttpResponse()

    module_with("rastro.sample.apis", wall_paint_view)

    assert view_violations(wall_paint_view) == [
        "rastro.sample.apis.wall_paint_view: view lives outside a views module",
    ]
