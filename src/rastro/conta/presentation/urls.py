from django.urls import path

from rastro.conta.presentation import views

urlpatterns = [
    path("", views.ContaView.as_view()),
    path("csrftoken", views.CsrfTokenView.as_view()),
    path("entrar", views.EntrarView.as_view()),
    path("cadastrar", views.CadastrarView.as_view()),
    path("sair", views.SairView.as_view()),
]
