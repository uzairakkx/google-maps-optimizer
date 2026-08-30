from __future__ import annotations

from app.worker.tasks import ping


def test_foundation_celery_task_executes() -> None:
    result = ping.apply().get()

    assert result == "pong"