from django.urls import path

from rastro.auth.presentation import views

urlpatterns = [
    path("me", views.me),
    path("sign_in", views.sign_in),
    path("sign_up", views.sign_up),
    path("sign_out", views.sign_out),
]
