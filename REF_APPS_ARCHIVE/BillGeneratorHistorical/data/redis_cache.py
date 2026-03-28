"""
Redis caching utilities for the Stream Bill Generator
This module provides Redis-based caching as an alternative to in-memory caching.
"""
import json
import time
from typing import Any, Dict, Optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

class RedisCache:
    """Redis-based cache with TTL support"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize the RedisCache
        
        Args:
            host (str): Redis host
            port (int): Redis port
            db (int): Redis database number
        """
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            print("Redis not available, using in-memory cache")
            return
            
        try:
            self.client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            # Test connection
            self.client.ping()
            print("Connected to Redis successfully")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in the cache with TTL
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (int): Time to live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not REDIS_AVAILABLE or self.client is None:
            return False
            
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
                
            result = self.client.setex(key, ttl, serialized_value)
            return result
        except Exception as e:
            print(f"Error setting cache value: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found or expired
        """
        if not REDIS_AVAILABLE or self.client is None:
            return None
            
        try:
            value = self.client.get(key)
            if value is None:
                return None
                
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Error getting cache value: {e}")
            return None
    
    def clear(self) -> bool:
        """
        Clear all cached values
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not REDIS_AVAILABLE or self.client is None:
            return False
            
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

# Hybrid cache that uses Redis when available, falls back to in-memory
class HybridCache:
    """Hybrid cache that uses Redis when available, falls back to in-memory"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """
        Initialize the HybridCache
        
        Args:
            redis_host (str): Redis host
            redis_port (int): Redis port
            redis_db (int): Redis database number
        """
        self.redis_cache = RedisCache(redis_host, redis_port, redis_db) if REDIS_AVAILABLE else None
        from data.cache_utils import InMemoryCache
        self.memory_cache = InMemoryCache()
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value in the cache with TTL
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (int): Time to live in seconds (default: 1 hour)
        """
        # Try Redis first
        if self.redis_cache is not None:
            success = self.redis_cache.set(key, value, ttl)
            if success:
                return
                
        # Fall back to in-memory cache
        self.memory_cache.set(key, value, ttl)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found or expired
        """
        # Try Redis first
        if self.redis_cache is not None:
            value = self.redis_cache.get(key)
            if value is not None:
                return value
                
        # Fall back to in-memory cache
        return self.memory_cache.get(key)
    
    def clear(self) -> None:
        """Clear all cached values"""
        if self.redis_cache is not None:
            self.redis_cache.clear()
        self.memory_cache.clear()

# Global hybrid cache instance
_hybrid_cache = HybridCache()

def get_cache() -> HybridCache:
    """Get the global hybrid cache instance"""
    return _hybrid_cache

def cache_bill_data(bill_id: str, bill_data: Dict[str, Any], ttl: int = 7200) -> None:
    """
    Cache bill data
    
    Args:
        bill_id (str): Bill ID
        bill_data (Dict[str, Any]): Bill data
        ttl (int): Time to live in seconds (default: 2 hours)
    """
    cache = get_cache()
    cache.set(f"bill_{bill_id}", bill_data, ttl)

def get_cached_bill_data(bill_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached bill data
    
    Args:
        bill_id (str): Bill ID
        
    Returns:
        Optional[Dict[str, Any]]: Cached bill data or None
    """
    cache = get_cache()
    return cache.get(f"bill_{bill_id}")

if __name__ == "__main__":
    # Example usage
    cache = get_cache()
    
    # Test setting and getting values
    test_data = {"bill_id": "12345", "amount": 1000.0, "items": ["item1", "item2"]}
    cache.set("test_bill", test_data, ttl=10)
    
    retrieved_data = cache.get("test_bill")
    print("Retrieved data:", retrieved_data)
    
    # Test expiration
    time.sleep(11)
    expired_data = cache.get("test_bill")
    print("Expired data:", expired_data)