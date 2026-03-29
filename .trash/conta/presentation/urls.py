from django.urls import path

from rastro.conta.presentation import views

urlpatterns = [
    path("", views.conta, name="conta"),
    path("entrar", views.entrar, name="entrar"),
    path("cadastrar", views.cadastrar, name="cadastrar"),
    path("sair", views.sair, name="sair"),
]
