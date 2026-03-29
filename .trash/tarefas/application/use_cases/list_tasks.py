from rastro.tarefas.domain.entities import Task
from rastro.tarefas.domain.repositories import TaskRepository
from rastro.tarefas.application.dto import ListTasksInput, TaskOutput


class ListTasksUseCase:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    def execute(self, input: ListTasksInput) -> list[TaskOutput]:
        tasks = self._task_repo.list_by_owner(input.owner_id)
        return [
            TaskOutput(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                owner_id=task.owner_id,
                created_at=task.created_at,
                updated_at=task.updated_at,
                deleted_at=task.deleted_at,
            )
            for task in tasks
        ]


def get_list_tasks_usecase() -> ListTasksUseCase:
    from rastro.tarefas.infrastructure.repositories import DjangoTaskRepository

    return ListTasksUseCase(DjangoTaskRepository())
