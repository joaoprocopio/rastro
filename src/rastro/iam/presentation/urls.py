from django.urls import path

from rastro.iam.presentation import views

urlpatterns = [
    path("identities", views.IdentitiesView.as_view()),
]
