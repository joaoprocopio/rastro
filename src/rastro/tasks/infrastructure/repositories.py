from typing import TYPE_CHECKING

from rastro.tasks.domain.entities import Task
from rastro.tasks.domain.repository import TaskRepository
from rastro.tasks.domain.value_objects import (
    TaskDescription,
    TaskDueDate,
    TaskPriority,
    TaskStatus,
    TaskTitle,
)
from rastro.tasks.infrastructure.mappers import DjangoToDomainTaskMapper
from rastro.tasks.infrastructure.models import TaskModel
from rastro_base.entity import Id

if TYPE_CHECKING:
    from rastro.tasks.infrastructure.models import TaskModel as TaskModelType


class DjangoTaskRepository(TaskRepository):
    def create(
        self,
        title: TaskTitle,
        description: TaskDescription,
        status: TaskStatus,
        priority: TaskPriority,
        due_date: TaskDueDate,
        owner_id: Id,
        assignee_id: Id | None,
    ) -> Task:
        task_model = TaskModel.objects.create(  # type: ignore[misc]
            title=title.value,
            description=description.value,
            status=status.value,
            priority=priority.value,
            due_date=due_date.value,
            owner_id=owner_id.value,
            assignee_id=assignee_id.value if assignee_id else None,
        )

        return DjangoToDomainTaskMapper.map(task_model)

    def get_by_id(self, id: Id) -> Task | None:
        try:
            task_model = TaskModel.objects.get(pk=id.value)  # type: ignore[misc]

            return DjangoToDomainTaskMapper.map(task_model)
        except TaskModel.DoesNotExist:
            return None

    def list_by_owner(self, owner_id: Id) -> list[Task]:
        task_models = TaskModel.objects.filter(owner_id=owner_id.value)  # type: ignore[misc]

        return [DjangoToDomainTaskMapper.map(tm) for tm in task_models]

    def list_by_assignee(self, assignee_id: Id) -> list[Task]:
        task_models = TaskModel.objects.filter(assignee_id=assignee_id.value)  # type: ignore[misc]

        return [DjangoToDomainTaskMapper.map(tm) for tm in task_models]

    def update(
        self,
        id: Id,
        title: TaskTitle | None = None,
        description: TaskDescription | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date: TaskDueDate | None = None,
        assignee_id: Id | None = None,
    ) -> Task:
        task_model = TaskModel.objects.get(pk=id.value)  # type: ignore[misc]

        if title is not None:
            task_model.title = title.value
        if description is not None:
            task_model.description = description.value
        if status is not None:
            task_model.status = status.value
        if priority is not None:
            task_model.priority = priority.value
        if due_date is not None:
            task_model.due_date = due_date.value
        if assignee_id is not None:
            task_model.assignee_id = assignee_id.value

        task_model.save()

        return DjangoToDomainTaskMapper.map(task_model)

    def delete(self, id: Id) -> None:
        TaskModel.objects.filter(pk=id.value).delete()  # type: ignore[misc]
