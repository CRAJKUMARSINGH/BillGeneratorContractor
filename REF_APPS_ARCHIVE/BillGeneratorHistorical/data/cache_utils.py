"""
Caching utilities for the Stream Bill Generator
This module provides caching mechanisms to improve performance.
"""
import json
import os
import time
from functools import lru_cache
from typing import Any, Dict, Optional

class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value in the cache with TTL
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (int): Time to live in seconds (default: 1 hour)
        """
        self._cache[key] = value
        self._timestamps[key] = time.time() + ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None
        
        # Check if expired
        if time.time() > self._timestamps.get(key, 0):
            # Remove expired entry
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            return None
        
        return self._cache[key]
    
    def clear(self) -> None:
        """Clear all cached values"""
        self._cache.clear()
        self._timestamps.clear()

# Global cache instance
_global_cache = InMemoryCache()

def get_cache() -> InMemoryCache:
    """Get the global cache instance"""
    return _global_cache

@lru_cache(maxsize=1024)
def get_reference_data_cached(ref_id: str) -> Dict[str, Any]:
    """
    Get reference data with LRU caching
    
    Args:
        ref_id (str): Reference ID
        
    Returns:
        Dict[str, Any]: Reference data
    """
    # This is a placeholder - in a real implementation, this would load from database
    # For now, we'll just return a simple structure
    return {
        "id": ref_id,
        "timestamp": time.time(),
        "data": f"Reference data for {ref_id}"
    }

def cache_bill_template(template_name: str, template_data: Dict[str, Any], ttl: int = 7200) -> None:
    """
    Cache a bill template
    
    Args:
        template_name (str): Name of the template
        template_data (Dict[str, Any]): Template data
        ttl (int): Time to live in seconds (default: 2 hours)
    """
    cache = get_cache()
    cache.set(f"template_{template_name}", template_data, ttl)

def get_cached_bill_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a cached bill template
    
    Args:
        template_name (str): Name of the template
        
    Returns:
        Optional[Dict[str, Any]]: Cached template data or None
    """
    cache = get_cache()
    return cache.get(f"template_{template_name}")

def log_usage(event: str, context: Dict[str, Any]) -> None:
    """
    Log usage metrics for telemetry (ethical, anonymized)
    
    Args:
        event (str): Event name
        context (Dict[str, Any]): Context data
    """
    log_entry = {
        "event": event,
        "time": time.time(),
        "context": context
    }
    
    # Append to log file
    try:
        with open("usage_log.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        # Silently fail to avoid disrupting main functionality
        pass

if __name__ == "__main__":
    # Example usage
    cache = get_cache()
    cache.set("test_key", "test_value", ttl=10)
    print(cache.get("test_key"))  # Should print "test_value"
    
    # Test expiration
    time.sleep(11)
    print(cache.get("test_key"))  # Should print None