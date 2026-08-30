from __future__ import annotations

from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.settings import get_settings


async def get_redis() -> AsyncIterator[Redis]:
    client: Redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()