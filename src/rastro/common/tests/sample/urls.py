from django.urls import path

from rastro.common.tests.sample import apis

# Django reads the handlers from the active ROOT_URLCONF, so this one re-exports them.
from rastro.urls import handler404, handler500  # noqa: F401

urlpatterns = [
    path("paint", apis.paint_api),
    path("paint/count", apis.paint_count_api),
    path("boom", apis.boom_api),
]
