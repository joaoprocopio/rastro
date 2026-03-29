from rastro.tarefas.domain.repositories import TaskRepository
from rastro.tarefas.domain.exceptions import TaskNotFoundError, TaskNotOwnedError
from rastro.tarefas.application.dto import GetTaskInput, TaskOutput


class GetTaskUseCase:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    def execute(self, input: GetTaskInput) -> TaskOutput:
        task = self._task_repo.get_by_id(input.task_id, input.owner_id)

        if task is None:
            raise TaskNotFoundError()

        if task.owner_id != input.owner_id:
            raise TaskNotOwnedError()

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


def get_get_task_usecase() -> GetTaskUseCase:
    from rastro.tarefas.infrastructure.repositories import DjangoTaskRepository

    return GetTaskUseCase(DjangoTaskRepository())
