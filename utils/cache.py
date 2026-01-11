"""Caching utilities for performance optimization"""

import time
import hashlib
import json
from typing import Any, Optional, Callable, TypeVar
from functools import wraps
from datetime import datetime, timedelta
from cachetools import TTLCache, LRUCache
import os

from utils.logging import get_logger
from utils.monitoring import get_monitoring

logger = get_logger(__name__)
monitor = get_monitoring()

T = TypeVar('T')


class CacheManager:
    """Centralized cache management"""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 7200,  # Increased from 3600 to 7200 for better hit rate
        cache_type: str = "ttl"
    ):
        """
        Initialize cache manager with optimized defaults
        
        Args:
            max_size: Maximum number of cache entries
            ttl_seconds: Time-to-live in seconds (optimized: 7200 = 2 hours)
            cache_type: Type of cache ("ttl" or "lru")
        """
        self.ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", ttl_seconds))
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        
        if cache_type == "ttl":
            self.cache = TTLCache(maxsize=max_size, ttl=self.ttl_seconds)
        else:
            self.cache = LRUCache(maxsize=max_size)
        
        logger.info("Cache manager initialized", maxsize=max_size, ttl=self.ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with performance tracking
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        try:
            value = self.cache.get(key)
            if value is not None:
                logger.debug("Cache hit", key=key)
                # Track cache hit if monitoring is available
                if hasattr(monitor, 'increment_counter'):
                    monitor.increment_counter("cache_hits", 1)
            else:
                logger.debug("Cache miss", key=key)
                # Track cache miss if monitoring is available
                if hasattr(monitor, 'increment_counter'):
                    monitor.increment_counter("cache_misses", 1)
            return value
        except KeyError:
            # Track cache miss if monitoring is available
            if hasattr(monitor, 'increment_counter'):
                monitor.increment_counter("cache_misses", 1)
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return
        
        try:
            self.cache[key] = value
        except Exception:
            pass  # Silently fail on cache errors
    
    def delete(self, key: str) -> None:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            MD5 hash of serialized arguments
        """
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
_cache_manager = CacheManager()


def cached(ttl_seconds: Optional[int] = None, key_func: Optional[Callable[..., str]] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to cache function results
    
    Args:
        ttl_seconds: Time-to-live in seconds (overrides default)
        key_func: Custom key generation function
        
    Example:
        @cached(ttl_seconds=300)
        def expensive_function(arg1, arg2):
            return expensive_computation(arg1, arg2)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _cache_manager.generate_key(
                    func.__name__, *args, **kwargs
                )
            
            # Try to get from cache
            cached_result = _cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            _cache_manager.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator
