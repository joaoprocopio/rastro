from django.contrib import admin
from django.urls import include, path

from rastro.users.interfaces.urls import urlpatterns as users_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/users/", include((users_urlpatterns, "rastro.users"))),
]
