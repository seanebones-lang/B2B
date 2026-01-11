"""Tests for caching utilities"""

import time
import pytest
from utils.cache import CacheManager, cached


class TestCacheManager:
    """Test cache manager"""
    
    def test_get_set(self):
        """Test basic get/set operations"""
        cache = CacheManager(max_size=10, ttl_seconds=60)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        assert cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """Test TTL expiration"""
        cache = CacheManager(max_size=10, ttl_seconds=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_delete(self):
        """Test cache deletion"""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test cache clearing"""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_generate_key(self):
        """Test cache key generation"""
        cache = CacheManager()
        key1 = cache.generate_key("func", "arg1", "arg2", kwarg1="value1")
        key2 = cache.generate_key("func", "arg1", "arg2", kwarg1="value1")
        assert key1 == key2  # Same inputs should generate same key
        
        key3 = cache.generate_key("func", "arg1", "arg2", kwarg1="value2")
        assert key1 != key3  # Different inputs should generate different keys


class TestCachedDecorator:
    """Test cached decorator"""
    
    def test_cached_function(self):
        """Test caching function results"""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - should execute
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call with same args - should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
        
        # Different args - should execute
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
