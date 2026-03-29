import random
from datetime import datetime
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist

from rastro.tarefas.domain.entities import Task
from rastro.tarefas.domain.value_objects import TaskStatus
from rastro.tarefas.domain.repositories import TaskRepository
from rastro.tarefas.infrastructure.models import TaskModel


class DjangoTaskRepository(TaskRepository):
    def get_by_id(self, task_id: int, owner_id: int) -> Task | None:
        try:
            task = TaskModel.active.get(id=task_id, owner_id=owner_id)
            return self._to_domain(task)
        except ObjectDoesNotExist:
            return None

    def list_by_owner(self, owner_id: int) -> list[Task]:
        tasks = TaskModel.active.filter(owner_id=owner_id)
        return [self._to_domain(task) for task in tasks]

    def create(
        self,
        title: str,
        description: str | None,
        status: TaskStatus,
        owner_id: int,
    ) -> Task:
        task = TaskModel.objects.create(
            title=title,
            description=description,
            status=status.value,
            owner_id=owner_id,
        )
        return self._to_domain(task)

    def update(
        self,
        task_id: int,
        owner_id: int,
        title: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
    ) -> Task:
        task = TaskModel.active.get(id=task_id, owner_id=owner_id)

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status.value

        task.save()
        return self._to_domain(task)

    def soft_delete(self, task_id: int, owner_id: int) -> bool:
        try:
            task = TaskModel.active.get(id=task_id, owner_id=owner_id)
            task.deleted_at = datetime.now()
            task.save()
            return True
        except ObjectDoesNotExist:
            return False

    def _to_domain(self, task_model: TaskModel) -> Task:
        return Task(
            id=task_model.id,
            title=task_model.title,
            description=task_model.description,
            status=TaskStatus(task_model.status),
            owner_id=task_model.owner_id,
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
            deleted_at=task_model.deleted_at,
        )
