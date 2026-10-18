from django.urls import include, path

from rastro.common.tests.sample import views

# Django reads the handlers from the active ROOT_URLCONF, so this one re-exports them.
from rastro.urls import handler404, handler500  # noqa: F401

sample_patterns = [
    path("paint", views.paint_apply_view, name="paint_apply"),
    path("paint/count", views.paint_count_view, name="paint_count"),
    path("paint/find", views.paint_find_view, name="paint_find"),
    path("boom", views.boom_raise_view, name="boom_raise"),
    path("wall", views.wall_paint_view, name="wall_paint"),
]

urlpatterns = [path("", include((sample_patterns, "sample")))]
