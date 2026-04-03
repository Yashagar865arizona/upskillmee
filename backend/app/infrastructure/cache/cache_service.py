"""
Location: ponder/backend/app/services/cache_service.py

Redis-based caching service for improved performance and scalability.
Features:
- Connection pooling for better resource management
- Health checks and automatic reconnection
- Serialization error handling
- Metrics tracking
"""

import redis
import json
import logging
from typing import Any, Optional, Dict, Union
import time
from ..config import settings
from ..monitoring.metrics import cache_metrics

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        try:
            self.redis: Optional[redis.Redis] = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
                password=settings.REDIS_PASSWORD,
                max_connections=10,
                health_check_interval=30
            )
            self.default_ttl = settings.CACHE_TTL
            self.namespace = settings.ENVIRONMENT
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            self.redis = None

    def _build_key(self, key: str) -> str:
        """Build namespaced cache key"""
        return f"{self.namespace}:{key}"

    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        try:
            if not self.redis:
                return None

            value = self.redis.get(self._build_key(key))

            if value:
                cache_metrics.record_hit(cache_type)
                try:
                    if isinstance(value, (str, bytes, bytearray)):
                        return json.loads(value)
                    return value
                except json.JSONDecodeError:
                    return value
            cache_metrics.record_miss(cache_type)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Redis operation: {str(e)}")
            return None
        finally:
            duration = time.time() - start_time
            cache_metrics.record_latency("get", duration)

    async def set(self, key: str, value: Any, expire: Optional[int] = None, cache_type: str = "default") -> bool:
        """Set value in cache with expiration"""
        start_time = time.time()
        try:
            if not self.redis:
                return False

            serialized = json.dumps(value) if not isinstance(value, (str, int, float)) else str(value)
            ttl = expire if expire is not None else self.default_ttl
            success = bool(self.redis.setex(self._build_key(key), ttl, serialized))

            if success:
                cache_metrics.record_operation("set", "success")
            return success
        except Exception as e:
            logger.error(f"Unexpected error in Redis operation: {str(e)}")
            cache_metrics.record_operation("set", "failure")
            return False
        finally:
            duration = time.time() - start_time
            cache_metrics.record_latency("set", duration)

    async def delete(self, key: str, cache_type: str = "default") -> bool:
        """Delete value from cache"""
        start_time = time.time()
        try:
            if not self.redis:
                return False

            success = bool(self.redis.delete(self._build_key(key)))

            if success:
                cache_metrics.record_operation("delete", "success")
            return success
        except Exception as e:
            logger.error(f"Unexpected error in Redis operation: {str(e)}")
            cache_metrics.record_operation("delete", "failure")
            return False
        finally:
            duration = time.time() - start_time
            cache_metrics.record_latency("delete", duration)

    async def clear_all(self) -> bool:
        """Clear all cached data in the current namespace."""
        try:
            if not self.redis:
                return False

            pattern = f"{self.namespace}:*"
            keys = self.redis.keys(pattern)
            if keys and isinstance(keys, list):
                # Convert keys to a list of strings if they aren't already
                key_list = [str(key) for key in keys]
                return bool(self.redis.delete(*key_list))
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            if not self.redis:
                return False
            return bool(self.redis.ping())
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
