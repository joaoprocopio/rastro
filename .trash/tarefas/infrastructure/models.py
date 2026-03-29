from django.db import models
from django.contrib.auth import get_user_model

from rastro.tarefas.domain.value_objects import TaskStatus


User = get_user_model()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TaskModel(models.Model):
    STATUS_CHOICES = [
        (TaskStatus.PENDING.value, "Pending"),
        (TaskStatus.IN_PROGRESS.value, "In Progress"),
        (TaskStatus.COMPLETED.value, "Completed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=TaskStatus.PENDING.value,
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active = SoftDeleteManager()

    class Meta:
        db_table = "tarefas_task"

    def __str__(self):
        return self.title
