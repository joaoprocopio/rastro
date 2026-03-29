from django.urls import path, include

urlpatterns = [
    path("v1/conta/", include("rastro.conta.presentation.urls")),
    path("v1/tarefas/", include("rastro.tarefas.presentation.urls")),
]
