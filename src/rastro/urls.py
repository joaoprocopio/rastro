from django.contrib import admin
from django.urls import include, path

from rastro.iam import urls as iam_urls
from rastro.iam.presentation import urls as old_iam_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/iam/", include(iam_urls)),
    path("api/v1/iam/", include(old_iam_urls)),
]

handler404 = "rastro.common.views.not_found"
handler500 = "rastro.common.views.server_error"
