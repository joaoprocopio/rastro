from django.urls import path

from rastro.iam.presentation import views

urlpatterns = [
    path("identities", views.IdentitiesView.as_view()),
    path("session", views.SessionView.as_view()),
    path("csrftoken", views.CsrfTokenView.as_view()),
]
