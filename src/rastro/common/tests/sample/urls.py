from django.urls import include, path

from rastro.common.tests.sample import views

# Django reads the handlers from the active ROOT_URLCONF, so this one re-exports them.
from rastro.urls import handler404, handler500  # noqa: F401

sample_patterns = [
    path("paint", views.paint_apply_view, name="paint_apply"),
    path("paint/count", views.paint_count_view, name="paint_count"),
    path("boom", views.boom_raise_view, name="boom_raise"),
]

urlpatterns = [path("", include((sample_patterns, "sample")))]
