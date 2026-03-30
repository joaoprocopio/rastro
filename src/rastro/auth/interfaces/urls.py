from django.urls import path

from rastro.auth.interfaces import views

urlpatterns = [
    path("sign_up", views.sign_up, name="sign_up"),
    path("sign_in", views.sign_in, name="sign_in"),
    path("sign_out", views.sign_out, name="sign_out"),
    path("me", views.me, name="me"),
]
