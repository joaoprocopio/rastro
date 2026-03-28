from django.contrib import admin
from django.urls import include, path

from rastro.api.exceptions import handle_404, handle_500

handler404 = handle_404
handler500 = handle_500

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("rastro.api.v1.urls")),
]
