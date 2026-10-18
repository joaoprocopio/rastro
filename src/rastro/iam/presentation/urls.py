from django.urls import path

from rastro.iam.presentation import views

urlpatterns = [
    path("session", views.SessionView.as_view()),
    path("csrftoken", views.CsrfTokenView.as_view()),
]
