"""
Redis Service - Simple cache for Cupido (optional)
"""
import json
from typing import Any, Optional

import redis.asyncio as redis

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RedisService:
    """Optional Redis service for caching."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.available = False

    async def connect(self) -> None:
        """Connect to Redis. Fails silently if not configured."""
        if not settings.REDIS_URL:
            logger.info("Redis not configured - running without cache")
            return

        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            self.available = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available (running without cache): {e}")
            self.redis_client = None
            self.available = False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis disconnected")

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        if not self.available:
            return None
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set a value in Redis with TTL."""
        if not self.available:
            return False
        try:
            await self.redis_client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self.available:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False


# Global instance
redis_service = RedisService()
