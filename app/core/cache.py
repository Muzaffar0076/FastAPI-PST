import json
import os
from typing import Optional, Any
import redis
from functools import wraps

# Redis connection - fallback to in-memory dict if Redis unavailable
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# Initialize in-memory cache (used as fallback)
_memory_cache = {}
redis_client = None

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except (redis.ConnectionError, redis.TimeoutError):
    REDIS_AVAILABLE = False
    redis_client = None
    print("Redis not available, using in-memory cache")


class CacheService:
    """Cache service for price computations with Redis fallback to in-memory"""
    
    @staticmethod
    def _get_key(prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        if REDIS_AVAILABLE:
            try:
                value = redis_client.get(key)
                return json.loads(value) if value else None
            except Exception:
                return None
        else:
            return _memory_cache.get(key)
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = CACHE_TTL) -> bool:
        """Set value in cache with TTL"""
        try:
            if REDIS_AVAILABLE:
                redis_client.setex(key, ttl, json.dumps(value))
            else:
                _memory_cache[key] = value
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        try:
            if REDIS_AVAILABLE:
                redis_client.delete(key)
            else:
                _memory_cache.pop(key, None)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern"""
        count = 0
        try:
            if REDIS_AVAILABLE:
                # Use scan_iter for better performance with large datasets
                for key in redis_client.scan_iter(match=pattern):
                    redis_client.delete(key)
                    count += 1
            else:
                # In-memory pattern matching
                # Pattern format: "price:*:product_id:*" or "price:product_id:*"
                product_id_str = str(pattern.split(':')[-2] if ':' in pattern else pattern.split('*')[1])
                # Find all keys that start with "price:" and contain the product_id
                keys_to_delete = [
                    k for k in _memory_cache.keys() 
                    if k.startswith("price:") and f":{product_id_str}:" in k
                ]
                for key in keys_to_delete:
                    _memory_cache.pop(key, None)
                    count += 1
        except Exception as e:
            print(f"Cache deletion error: {e}")
            pass
        return count
    
    @staticmethod
    def invalidate_product(product_id: int):
        """Invalidate all cache entries for a product"""
        # Pattern: price:product_id:quantity:currency:tax:rounding
        # We'll delete all keys starting with "price:" that contain the product_id
        count = 0
        try:
            if REDIS_AVAILABLE:
                pattern = f"price:*:{product_id}:*"
                for key in redis_client.scan_iter(match=pattern):
                    redis_client.delete(key)
                    count += 1
            else:
                # In-memory: delete all keys containing product_id
                product_id_str = str(product_id)
                keys_to_delete = [
                    k for k in _memory_cache.keys() 
                    if k.startswith("price:") and f":{product_id_str}:" in k
                ]
                for key in keys_to_delete:
                    _memory_cache.pop(key, None)
                    count += 1
        except Exception as e:
            print(f"Cache invalidation error: {e}")
        return count
    
    @staticmethod
    def invalidate_promotion(promotion_id: int, product_id: int):
        """Invalidate cache for a product when promotion changes"""
        CacheService.invalidate_product(product_id)


def cache_result(prefix: str, ttl: int = CACHE_TTL):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = CacheService._get_key(prefix, *args, *sorted(kwargs.items()))
            
            # Try to get from cache
            cached = CacheService.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Store in cache
            CacheService.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

