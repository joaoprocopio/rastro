from django.urls import path

from rastro.common.tests.sample import apis

urlpatterns = [
    path("paint", apis.paint_api),
    path("paint/count", apis.paint_count_api),
]
