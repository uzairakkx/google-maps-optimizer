from __future__ import annotations

from app.core.logging import logger
from app.worker.celery_app import celery_app


@celery_app.task(name="foundation.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    """Minimal task used to verify Celery-to-Redis worker plumbing."""
    logger.info("foundation_task_executed", task="foundation.ping")
    return "pong"