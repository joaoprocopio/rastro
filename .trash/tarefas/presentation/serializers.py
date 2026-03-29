from rastro.tarefas.application.dto import TaskOutput


def serialize_task(task: TaskOutput) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "owner_id": task.owner_id,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "deleted_at": task.deleted_at.isoformat() if task.deleted_at else None,
    }


def serialize_tasks(tasks: list[TaskOutput]) -> list[dict]:
    return [serialize_task(task) for task in tasks]
