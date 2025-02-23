from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from bson import ObjectId
from redis import asyncio as aioredis
from app.core.config import settings
from app.core.logger import db_logger as logger

class RedisClient:
    def __init__(self):
        logger.debug(f"Initializing Redis client at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        # Construct Redis URL with password
        redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        self.redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis client initialized")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = None
    ) -> bool:
        """Set value in Redis with optional expiration"""
        try:
            value = self._prepare_for_json(value)
            value_str = json.dumps(value)
            
            if expire:
                await self.redis.setex(key, expire, value_str)
            else:
                await self.redis.set(key, value_str)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {str(e)}")
            return False

    def _prepare_for_json(self, obj: Any) -> Any:
        """Convert a model dict to a JSON-serializable dict"""
        if isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj