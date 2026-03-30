from datetime import datetime

from rastro.tasks.domain.errors import (
    InvalidTaskDescriptionError,
    InvalidTaskPriorityError,
    InvalidTaskStatusError,
    InvalidTaskTitleError,
)
from rastro_base.value_object import ValueObject


class TaskTitle(ValueObject[str]):
    def validate(self) -> None:
        if len(self.value) < 1 or len(self.value) > 200:
            raise InvalidTaskTitleError()


class TaskDescription(ValueObject[str | None]):
    def validate(self) -> None:
        if self.value is not None and len(self.value) > 2000:
            raise InvalidTaskDescriptionError()


# TODO: enum, maybe?
class TaskStatus(ValueObject[str]):
    VALID_STATUSES = frozenset({"OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CLOSED"})

    def validate(self) -> None:
        if self.value not in self.VALID_STATUSES:
            raise InvalidTaskStatusError()


class TaskPriority(ValueObject[str]):
    VALID_PRIORITIES = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})

    def validate(self) -> None:
        if self.value not in self.VALID_PRIORITIES:
            raise InvalidTaskPriorityError()


class TaskDueDate(ValueObject[datetime | None]):
    def validate(self) -> None:
        pass
