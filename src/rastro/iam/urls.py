from django.urls import path

from rastro.iam import apis

urlpatterns = [
    path("session/start", apis.session_start_api),
]
