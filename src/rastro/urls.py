from django.contrib import admin
from django.urls import include, path

from rastro.auth.presentation.urls import urlpatterns as auth_urlpatterns
from rastro.tasks.presentation.urls import urlpatterns as tasks_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include((auth_urlpatterns, "rastro.auth"))),
    path("api/v1/tasks/", include((tasks_urlpatterns, "rastro.tasks"))),
]
