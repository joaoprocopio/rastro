from django.contrib import admin
from django.urls import include, path

from rastro.conta.presentation import urls as conta_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/conta/", include(conta_urls)),
]
