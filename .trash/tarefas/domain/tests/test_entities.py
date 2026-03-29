import pytest

from rastro.tarefas.domain.entities import Task, TaskStatus


def test_task_creation():
    from datetime import datetime

    task = Task(
        id=1,
        title="Test Task",
        description="A test task",
        status=TaskStatus.PENDING,
        owner_id=1,
        created_at=datetime.now(),
    )

    assert task.id == 1
    assert task.title == "Test Task"
    assert task.description == "A test task"
    assert task.status == TaskStatus.PENDING
    assert task.owner_id == 1


def test_task_is_frozen():
    from datetime import datetime

    task = Task(
        id=1,
        title="Test Task",
        description="A test task",
        status=TaskStatus.PENDING,
        owner_id=1,
        created_at=datetime.now(),
    )

    with pytest.raises(Exception):
        task.title = "New Title"
