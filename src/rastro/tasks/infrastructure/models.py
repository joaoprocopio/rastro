from django.db import models

from rastro.tasks.domain.value_objects import TaskPriority, TaskStatus


class TaskModel(models.Model):
    STATUS_CHOICES = [(status, status) for status in TaskStatus.VALID_STATUSES]
    PRIORITY_CHOICES = [
        (priority, priority) for priority in TaskPriority.VALID_PRIORITIES
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="MEDIUM"
    )
    due_date = models.DateTimeField(null=True, blank=True)
    owner_id = models.IntegerField()
    assignee_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
