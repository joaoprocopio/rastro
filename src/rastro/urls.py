from django.contrib import admin
from django.urls import include, path

from rastro.iam.presentation import urls as iam_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/iam/", include(iam_urls)),
]
