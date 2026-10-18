from django.contrib import admin
from django.urls import include, path

from rastro.iam import urls as iam_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/iam/", include(iam_urls)),
]

handler404 = "rastro.common.views.not_found_view"
handler500 = "rastro.common.views.server_error_view"
