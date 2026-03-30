from django.contrib import admin
from django.urls import include, path

from rastro.auth.interfaces.urls import urlpatterns as auth_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include((auth_urlpatterns, "rastro.auth"))),
]
