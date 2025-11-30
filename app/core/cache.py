import redis
from typing import Any, Optional
import json

# Try to connect to Redis, fall back to in-memory cache
REDIS_AVAILABLE = False
redis_client = None

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except (redis.ConnectionError, redis.exceptions.ConnectionError):
    # Redis not available, use in-memory cache
    REDIS_AVAILABLE = False
    redis_client = None

# In-memory cache fallback
_memory_cache = {}


class CacheService:
    """Cache service with Redis primary and in-memory fallback"""

    @staticmethod
    def _get_key(*args) -> str:
        """Generate cache key from arguments"""
        return ":".join(str(arg) for arg in args)

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        if REDIS_AVAILABLE and redis_client:
            try:
                value = redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass

        # Fallback to memory cache
        return _memory_cache.get(key)

    @staticmethod
    def set(key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)"""
        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.setex(key, ttl, json.dumps(value))
                return True
            except Exception:
                pass

        # Fallback to memory cache (note: TTL not enforced in memory)
        _memory_cache[key] = value
        return True

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.delete(key)
            except Exception:
                pass

        # Also delete from memory cache
        _memory_cache.pop(key, None)
        return True

    @staticmethod
    def invalidate_product(product_id: int) -> int:
        """Invalidate all cache entries for a product"""
        count = 0
        pattern = f"price:{product_id}:*"

        if REDIS_AVAILABLE and redis_client:
            try:
                for key in redis_client.scan_iter(match=pattern):
                    redis_client.delete(key)
                    count += 1
            except Exception:
                pass

        # Also clear from memory cache
        keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(f"price:{product_id}:")]
        for key in keys_to_delete:
            _memory_cache.pop(key, None)
            count += 1

        return count

    @staticmethod
    def clear_all() -> int:
        """Clear all cache entries"""
        count = 0

        if REDIS_AVAILABLE and redis_client:
            try:
                for key in redis_client.scan_iter(match="price:*"):
                    redis_client.delete(key)
                    count += 1
            except Exception:
                pass

        # Clear memory cache
        keys = [k for k in _memory_cache.keys() if k.startswith("price:")]
        for key in keys:
            _memory_cache.pop(key, None)
            count += 1

        return count
