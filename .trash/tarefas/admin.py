from django.contrib import admin

from .infrastructure.models import TaskModel


@admin.register(TaskModel)
class TaskModelAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "status", "owner", "created_at", "deleted_at"]
    list_filter = ["status", "created_at", "deleted_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
