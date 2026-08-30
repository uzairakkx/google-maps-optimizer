from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_redis
from app.db.session import get_db_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Confirm that the API process is running."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict[str, object]:
    """Confirm required infrastructure can be reached without exposing details."""
    database_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    try:
        redis_ok = bool(await redis.ping())
    except Exception:
        redis_ok = False

    if not database_ok or not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "database": database_ok, "redis": redis_ok},
        )
    return {"status": "ok", "dependencies": {"database": "ok", "redis": "ok"}}