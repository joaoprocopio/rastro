from rastro_base.error import BaseError


class TaskNotFoundError(BaseError):
    code = "TASK_NOT_FOUND"


class TaskPermissionError(BaseError):
    code = "TASK_PERMISSION_ERROR"


class InvalidTaskTitleError(BaseError):
    code = "TASK_INVALID_TITLE"


class InvalidTaskDescriptionError(BaseError):
    code = "TASK_INVALID_DESCRIPTION"


class InvalidTaskStatusError(BaseError):
    code = "TASK_INVALID_STATUS"


class InvalidTaskPriorityError(BaseError):
    code = "TASK_INVALID_PRIORITY"


class AlwaysBreakError(BaseError):
    code = "TASK_ALWAYS_BREAK"


class Break50PercentError(BaseError):
    code = "TASK_BREAK_FIFTY_PERCENT"


class BreakRandomlyError(BaseError):
    code = "TASK_BREAK_RANDOMLY"
