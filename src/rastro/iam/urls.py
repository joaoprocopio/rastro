from django.urls import path

from rastro.iam import apis

urlpatterns = [
    path("identities/register", apis.identity_register_api),
    path("session/start", apis.session_start_api),
]
