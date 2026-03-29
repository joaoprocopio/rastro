from rastro.tarefas.domain.entities import Task
from rastro.tarefas.domain.value_objects import TaskStatus
from rastro.tarefas.domain.repositories import TaskRepository
from rastro.tarefas.application.dto import CreateTaskInput, TaskOutput
from rastro.tarefas.application.exceptions import TaskValidationError


class CreateTaskUseCase:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    def execute(self, input: CreateTaskInput) -> TaskOutput:
        if not input.title or len(input.title.strip()) < 1:
            raise TaskValidationError("Title is required")

        if len(input.title) > 200:
            raise TaskValidationError("Title must be at most 200 characters")

        task = self._task_repo.create(
            title=input.title,
            description=input.description,
            status=TaskStatus.PENDING,
            owner_id=input.owner_id,
        )

        return TaskOutput(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            owner_id=task.owner_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            deleted_at=task.deleted_at,
        )


def get_create_task_usecase() -> CreateTaskUseCase:
    from rastro.tarefas.infrastructure.repositories import DjangoTaskRepository

    return CreateTaskUseCase(DjangoTaskRepository())
