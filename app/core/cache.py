import redis
from typing import Any, Optional
import json
REDIS_AVAILABLE = False
redis_client = None
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except (redis.ConnectionError, redis.exceptions.ConnectionError):
    REDIS_AVAILABLE = False
    redis_client = None
_memory_cache = {}

class CacheService:

    @staticmethod
    def _get_key(*args) -> str:
        return ':'.join((str(arg) for arg in args))

    @staticmethod
    def get(key: str) -> Optional[Any]:
        if REDIS_AVAILABLE and redis_client:
            try:
                value = redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        return _memory_cache.get(key)

    @staticmethod
    def set(key: str, value: Any, ttl: int=3600) -> bool:
        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.setex(key, ttl, json.dumps(value))
                return True
            except Exception:
                pass
        _memory_cache[key] = value
        return True

    @staticmethod
    def delete(key: str) -> bool:
        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)
        return True

    @staticmethod
    def invalidate_product(product_id: int) -> int:
        count = 0
        pattern = f'price:{product_id}:*'
        if REDIS_AVAILABLE and redis_client:
            try:
                for key in redis_client.scan_iter(match=pattern):
                    redis_client.delete(key)
                    count += 1
            except Exception:
                pass
        keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(f'price:{product_id}:')]
        for key in keys_to_delete:
            _memory_cache.pop(key, None)
            count += 1
        return count

    @staticmethod
    def clear_all() -> int:
        count = 0
        if REDIS_AVAILABLE and redis_client:
            try:
                for key in redis_client.scan_iter(match='price:*'):
                    redis_client.delete(key)
                    count += 1
            except Exception:
                pass
        keys = [k for k in _memory_cache.keys() if k.startswith('price:')]
        for key in keys:
            _memory_cache.pop(key, None)
            count += 1
        return count