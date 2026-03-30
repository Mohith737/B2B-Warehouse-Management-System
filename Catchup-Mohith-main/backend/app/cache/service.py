# /home/mohith/Catchup-Mohith/backend/app/cache/service.py
import logging
from typing import Any

import redis.asyncio as aioredis
from backend.app.core.config import settings
from redis.asyncio import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self._cache_pool = ConnectionPool.from_url(
            settings.redis_url,
            db=settings.redis_cache_db,
            decode_responses=True,
            max_connections=20,
        )
        self._auth_pool = ConnectionPool.from_url(
            settings.redis_url,
            db=settings.redis_auth_db,
            decode_responses=True,
            max_connections=20,
        )

    def _get_client(self, db: int) -> aioredis.Redis:
        pool = self._auth_pool if db == settings.redis_auth_db else self._cache_pool
        return aioredis.Redis(connection_pool=pool)

    def _log_redis_error(self, operation: str, target: str, error: Any) -> None:
        logger.warning(f"Redis {operation} failed for {target}: {error}")

    async def get(self, key: str, db: int = 0) -> str | None:
        try:
            client = self._get_client(db)
            return await client.get(key)
        except RedisError as e:
            self._log_redis_error("GET", f"key={key}", e)
            return None

    async def set(self, key: str, value: str, ttl: int, db: int = 0) -> bool:
        try:
            client = self._get_client(db)
            await client.setex(key, ttl, value)
            return True
        except RedisError as e:
            self._log_redis_error("SET", f"key={key}", e)
            return False

    async def delete(self, key: str, db: int = 0) -> bool:
        try:
            client = self._get_client(db)
            await client.delete(key)
            return True
        except RedisError as e:
            self._log_redis_error("DELETE", f"key={key}", e)
            return False

    async def delete_pattern(self, pattern: str, db: int = 0) -> int:
        deleted = 0
        try:
            client = self._get_client(db)
            cursor = 0
            while True:
                cursor, keys = await client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )
                if keys:
                    pipe = client.pipeline()
                    for key in keys:
                        pipe.delete(key)
                    await pipe.execute()
                    deleted += len(keys)
                if cursor == 0:
                    break
            return deleted
        except RedisError as e:
            self._log_redis_error("DELETE_PATTERN", f"pattern={pattern}", e)
            return 0

    async def acquire_lock(self, key: str, ttl: int, db: int = 0) -> bool:
        try:
            client = self._get_client(db)
            result = await client.set(key, "1", nx=True, ex=ttl)
            return result is True
        except RedisError as e:
            self._log_redis_error("ACQUIRE_LOCK", f"key={key}", e)
            return False

    async def release_lock(self, key: str, db: int = 0) -> bool:
        try:
            client = self._get_client(db)
            await client.delete(key)
            return True
        except RedisError as e:
            self._log_redis_error("RELEASE_LOCK", f"key={key}", e)
            return False

    async def increment(self, key: str, db: int = 0) -> int | None:
        try:
            client = self._get_client(db)
            return await client.incr(key)
        except RedisError as e:
            self._log_redis_error("INCR", f"key={key}", e)
            return None


cache_service = CacheService()
