from django.urls import path

from rastro.users import views

urlpatterns = [
    path("", views.current_user, name="current_user"),
    # path("entrar", views.entrar, name="entrar"),
    # path("cadastrar", views.cadastrar, name="cadastrar"),
    # path("sair", views.sair, name="sair"),
]
