from typing import TYPE_CHECKING

from rastro.tasks.domain.entities import Task
from rastro.tasks.domain.value_objects import (
    TaskDescription,
    TaskDueDate,
    TaskPriority,
    TaskStatus,
    TaskTitle,
)
from rastro_base.entity import Id
from rastro_base.mapper import Mapper

if TYPE_CHECKING:
    from rastro.tasks.infrastructure.models import TaskModel as TaskModelType


class DjangoToDomainTaskMapper(Mapper["TaskModelType", Task]):
    @staticmethod
    def map(input: "TaskModelType") -> Task:
        return Task(
            id=Id(input.pk),
            title=TaskTitle(input.title),
            description=TaskDescription(input.description),
            status=TaskStatus(input.status),
            priority=TaskPriority(input.priority),
            due_date=TaskDueDate(input.due_date),
            owner_id=Id(input.owner_id),
            assignee_id=Id(input.assignee_id) if input.assignee_id else None,
        )


class DomainToDjangoTaskMapper(Mapper[Task, "TaskModelType"]):
    @staticmethod
    def map(input: Task) -> "TaskModelType":
        from rastro.tasks.infrastructure.models import TaskModel

        return TaskModel(
            id=input.id.value,
            title=input.title.value,
            description=input.description.value,
            status=input.status.value,
            priority=input.priority.value,
            due_date=input.due_date.value,
            owner_id=input.owner_id.value,
            assignee_id=input.assignee_id.value if input.assignee_id else None,
        )
