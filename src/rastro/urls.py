from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/conta/", include("rastro.conta.presentation.urls")),
    path("api/v1/tarefas/", include("rastro.tarefas.urls")),
]
