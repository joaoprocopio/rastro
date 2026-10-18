from django.urls import path

from rastro.iam import views

app_name = "iam"

urlpatterns = [
    path(
        "identities/register",
        views.identity_register_view,
        name="identity_register",
    ),
    path("session", views.session_current_view, name="session_current"),
    path("session/start", views.session_start_view, name="session_start"),
    path("session/end", views.session_end_view, name="session_end"),
    path("csrf", views.csrf_get_view, name="csrf_get"),
]
