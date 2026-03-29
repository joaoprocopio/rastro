from rastro.tarefas.domain.repositories import TaskRepository
from rastro.tarefas.domain.exceptions import (
    TaskNotFoundError,
    TaskNotOwnedError,
    TaskAlreadyDeletedError,
)
from rastro.tarefas.application.dto import DeleteTaskInput


class DeleteTaskUseCase:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    def execute(self, input: DeleteTaskInput) -> bool:
        task = self._task_repo.get_by_id(input.task_id, input.owner_id)

        if task is None:
            raise TaskNotFoundError()

        if task.owner_id != input.owner_id:
            raise TaskNotOwnedError()

        if task.deleted_at is not None:
            raise TaskAlreadyDeletedError()

        return self._task_repo.soft_delete(input.task_id, input.owner_id)


def get_delete_task_usecase() -> DeleteTaskUseCase:
    from rastro.tarefas.infrastructure.repositories import DjangoTaskRepository

    return DeleteTaskUseCase(DjangoTaskRepository())
