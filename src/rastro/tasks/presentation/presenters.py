from typing import TypedDict

from rastro.tasks.application.dtos import TaskOutput
from rastro_base.presenter import Presenter


class TaskPublic(TypedDict):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    due_date: str | None
    owner_id: int
    assignee_id: int | None


class TaskListPublic(TypedDict):
    tasks: list[TaskPublic]


class TaskPresenter(Presenter[TaskOutput, TaskPublic]):
    @staticmethod
    def present(private: TaskOutput) -> TaskPublic:
        return TaskPublic(
            id=private.id,
            title=private.title,
            description=private.description,
            status=private.status,
            priority=private.priority,
            due_date=private.due_date.isoformat() if private.due_date else None,
            owner_id=private.owner_id,
            assignee_id=private.assignee_id,
        )


class TaskListPresenter(Presenter[list[TaskOutput], TaskListPublic]):
    @staticmethod
    def present(private: list[TaskOutput]) -> TaskListPublic:
        return TaskListPublic(tasks=[TaskPresenter.present(task) for task in private])
