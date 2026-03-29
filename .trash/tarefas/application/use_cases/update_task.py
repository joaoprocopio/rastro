from rastro.tarefas.domain.entities import Task
from rastro.tarefas.domain.repositories import TaskRepository
from rastro.tarefas.domain.exceptions import TaskNotFoundError, TaskNotOwnedError
from rastro.tarefas.application.dto import UpdateTaskInput, TaskOutput


class UpdateTaskUseCase:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    def execute(self, input: UpdateTaskInput) -> TaskOutput:
        task = self._task_repo.get_by_id(input.task_id, input.owner_id)

        if task is None:
            raise TaskNotFoundError()

        if task.owner_id != input.owner_id:
            raise TaskNotOwnedError()

        updated_task = self._task_repo.update(
            task_id=input.task_id,
            owner_id=input.owner_id,
            title=input.title,
            description=input.description,
            status=input.status,
        )

        return TaskOutput(
            id=updated_task.id,
            title=updated_task.title,
            description=updated_task.description,
            status=updated_task.status,
            owner_id=updated_task.owner_id,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at,
            deleted_at=updated_task.deleted_at,
        )


def get_update_task_usecase() -> UpdateTaskUseCase:
    from rastro.tarefas.infrastructure.repositories import DjangoTaskRepository

    return UpdateTaskUseCase(DjangoTaskRepository())
