from rastro.tasks.application.dtos import CreateTaskInput, TaskOutput, UpdateTaskInput
from rastro.tasks.domain.entities import Task
from rastro.tasks.domain.errors import TaskNotFoundError, TaskPermissionError
from rastro.tasks.domain.repository import TaskRepository
from rastro.tasks.domain.value_objects import (
    TaskDescription,
    TaskDueDate,
    TaskPriority,
    TaskStatus,
    TaskTitle,
)
from rastro_base.entity import Id
from rastro_base.use_case import UseCase


class CreateTaskUseCase(UseCase[tuple[Id, CreateTaskInput], TaskOutput]):
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def execute(self, input: tuple[Id, CreateTaskInput]) -> TaskOutput:
        owner_id, task_input = input
        task = self.repository.create(
            title=TaskTitle(task_input.title),
            description=TaskDescription(task_input.description),
            status=TaskStatus(task_input.status),
            priority=TaskPriority(task_input.priority),
            due_date=TaskDueDate(task_input.due_date),
            owner_id=owner_id,
            assignee_id=Id(task_input.assignee_id) if task_input.assignee_id else None,
        )

        return TaskOutput(
            id=task.id.value,
            title=task.title.value,
            description=task.description.value,
            status=task.status.value,
            priority=task.priority.value,
            due_date=task.due_date.value,
            owner_id=task.owner_id.value,
            assignee_id=task.assignee_id.value if task.assignee_id else None,
        )


class ListTasksUseCase(UseCase[Id, list[TaskOutput]]):
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def execute(self, input: Id) -> list[TaskOutput]:
        tasks = self.repository.list_by_assignee(input)

        return [
            TaskOutput(
                id=task.id.value,
                title=task.title.value,
                description=task.description.value,
                status=task.status.value,
                priority=task.priority.value,
                due_date=task.due_date.value,
                owner_id=task.owner_id.value,
                assignee_id=task.assignee_id.value if task.assignee_id else None,
            )
            for task in tasks
        ]


class GetTaskUseCase(UseCase[tuple[Id, Id], TaskOutput]):
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def execute(self, input: tuple[Id, Id]) -> TaskOutput:
        task_id, user_id = input
        task = self.repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFoundError()

        if task.owner_id != user_id:
            raise TaskPermissionError()

        return TaskOutput(
            id=task.id.value,
            title=task.title.value,
            description=task.description.value,
            status=task.status.value,
            priority=task.priority.value,
            due_date=task.due_date.value,
            owner_id=task.owner_id.value,
            assignee_id=task.assignee_id.value if task.assignee_id else None,
        )


class UpdateTaskUseCase(UseCase[tuple[Id, Id, UpdateTaskInput], TaskOutput]):
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def execute(self, input: tuple[Id, Id, UpdateTaskInput]) -> TaskOutput:
        task_id, user_id, update_input = input
        task = self.repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFoundError()

        if task.owner_id != user_id:
            raise TaskPermissionError()

        updated_task = self.repository.update(
            id=task_id,
            title=TaskTitle(update_input.title) if update_input.title else None,
            description=TaskDescription(update_input.description)
            if update_input.description is not None
            else None,
            status=TaskStatus(update_input.status) if update_input.status else None,
            priority=TaskPriority(update_input.priority)
            if update_input.priority
            else None,
            due_date=TaskDueDate(update_input.due_date)
            if update_input.due_date is not None
            else None,
            assignee_id=Id(update_input.assignee_id)
            if update_input.assignee_id
            else None,
        )

        return TaskOutput(
            id=updated_task.id.value,
            title=updated_task.title.value,
            description=updated_task.description.value,
            status=updated_task.status.value,
            priority=updated_task.priority.value,
            due_date=updated_task.due_date.value,
            owner_id=updated_task.owner_id.value,
            assignee_id=updated_task.assignee_id.value
            if updated_task.assignee_id
            else None,
        )


class DeleteTaskUseCase(UseCase[tuple[Id, Id], None]):
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def execute(self, input: tuple[Id, Id]) -> None:
        task_id, user_id = input
        task = self.repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFoundError()

        if task.owner_id != user_id:
            raise TaskPermissionError()

        self.repository.delete(task_id)
