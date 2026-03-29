class TaskNotFoundError(Exception):
    pass


class TaskNotOwnedError(Exception):
    pass


class TaskAlreadyDeletedError(Exception):
    pass
