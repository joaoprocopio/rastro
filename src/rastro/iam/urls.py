from django.urls import path

from rastro.iam import apis

urlpatterns = [
    path("session", apis.session_current_api),
    path("session/start", apis.session_start_api),
    path("session/end", apis.session_end_api),
    path("csrf", apis.csrf_get_api),
]
