from django.urls import path

from rastro.tarefas.presentation import views

urlpatterns = [
    path("", views.list_tasks, name="list_tasks"),
    path("create", views.create_task, name="create_task"),
    path("<int:task_id>", views.get_task, name="get_task"),
    path("<int:task_id>/update", views.update_task, name="update_task"),
    path("<int:task_id>/delete", views.delete_task, name="delete_task"),
    path("always-break", views.always_break_endpoint, name="always_break"),
    path("break-50-percent", views.break_50_percent_endpoint, name="break_50_percent"),
    path("break-randomly", views.break_randomly_endpoint, name="break_randomly"),
]
