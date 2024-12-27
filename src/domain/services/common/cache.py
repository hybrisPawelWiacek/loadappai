"""Cache service implementation.

This module implements caching functionality.
It provides:
- Multi-level caching
- Cache invalidation
- TTL management
- Cache statistics
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
import json
import threading
import time

from src.domain.services.common.base import BaseService

class CacheService(BaseService):
    """Service for caching data.
    
    This service is responsible for:
    - Managing cache entries
    - Cache invalidation
    - TTL enforcement
    - Cache statistics
    """
    
    def __init__(
        self,
        redis_client: Optional['RedisClient'] = None,
        max_memory_items: int = 10000,
        default_ttl: int = 3600
    ):
        """Initialize cache service.
        
        Args:
            redis_client: Optional Redis client
            max_memory_items: Maximum items in memory cache
            default_ttl: Default TTL in seconds
        """
        super().__init__()
        self._redis = redis_client
        self._memory_cache: Dict[str, Any] = {}
        self._memory_ttl: Dict[str, float] = {}
        self._memory_hits: Dict[str, int] = {}
        self._max_items = max_memory_items
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        self._log_entry("get", key=key)
        
        try:
            # Try memory cache first
            with self._lock:
                if key in self._memory_cache:
                    if self._is_valid(key):
                        self._memory_hits[key] = (
                            self._memory_hits.get(key, 0) + 1
                        )
                        value = self._memory_cache[key]
                        self._log_exit("get", "memory_hit")
                        return value
                    else:
                        # Remove expired entry
                        self._remove_memory_entry(key)
            
            # Try Redis if available
            if self._redis:
                value = self._redis.get(key)
                if value is not None:
                    # Cache in memory
                    self.set(
                        key,
                        value,
                        self._redis.ttl(key)
                    )
                    self._log_exit("get", "redis_hit")
                    return value
            
            self._log_exit("get", "miss")
            return default
            
        except Exception as e:
            self._log_error("get", e)
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set cache value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds
            
        Returns:
            True if successful
        """
        self._log_entry("set", key=key, ttl=ttl)
        
        try:
            ttl = ttl or self._default_ttl
            
            # Set in Redis if available
            if self._redis:
                success = self._redis.set(
                    key,
                    value,
                    ex=ttl
                )
                if not success:
                    self._log_exit("set", "redis_fail")
                    return False
            
            # Set in memory cache
            with self._lock:
                # Check if we need to make space
                if (
                    len(self._memory_cache) >= self._max_items and
                    key not in self._memory_cache
                ):
                    self._evict_entries()
                
                self._memory_cache[key] = value
                self._memory_ttl[key] = time.time() + ttl
                self._memory_hits[key] = 0
            
            self._log_exit("set", "success")
            return True
            
        except Exception as e:
            self._log_error("set", e)
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        self._log_entry("delete", key=key)
        
        try:
            deleted = False
            
            # Delete from memory
            with self._lock:
                if key in self._memory_cache:
                    self._remove_memory_entry(key)
                    deleted = True
            
            # Delete from Redis
            if self._redis:
                redis_deleted = self._redis.delete(key) > 0
                deleted = deleted or redis_deleted
            
            self._log_exit("delete", deleted)
            return deleted
            
        except Exception as e:
            self._log_error("delete", e)
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful
        """
        self._log_entry("clear")
        
        try:
            # Clear memory cache
            with self._lock:
                self._memory_cache.clear()
                self._memory_ttl.clear()
                self._memory_hits.clear()
            
            # Clear Redis if available
            if self._redis:
                self._redis.flushdb()
            
            self._log_exit("clear", "success")
            return True
            
        except Exception as e:
            self._log_error("clear", e)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        self._log_entry("get_stats")
        
        try:
            stats = {
                "memory_cache": {
                    "size": len(self._memory_cache),
                    "max_size": self._max_items,
                    "hits": sum(self._memory_hits.values()),
                    "items": len(self._memory_cache),
                    "expired": self._count_expired()
                }
            }
            
            # Add Redis stats if available
            if self._redis:
                info = self._redis.info()
                stats["redis"] = {
                    "connected": True,
                    "used_memory": info.get("used_memory", 0),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "keys": self._redis.dbsize()
                }
            
            self._log_exit("get_stats", stats)
            return stats
            
        except Exception as e:
            self._log_error("get_stats", e)
            return {"error": str(e)}
    
    def _is_valid(self, key: str) -> bool:
        """Check if cache entry is valid.
        
        Args:
            key: Cache key
            
        Returns:
            True if valid
        """
        return (
            key in self._memory_ttl and
            time.time() < self._memory_ttl[key]
        )
    
    def _count_expired(self) -> int:
        """Count expired cache entries.
        
        Returns:
            Number of expired entries
        """
        now = time.time()
        return sum(
            1 for ttl in self._memory_ttl.values()
            if ttl < now
        )
    
    def _remove_memory_entry(self, key: str) -> None:
        """Remove entry from memory cache.
        
        Args:
            key: Cache key
        """
        self._memory_cache.pop(key, None)
        self._memory_ttl.pop(key, None)
        self._memory_hits.pop(key, None)
    
    def _evict_entries(self) -> None:
        """Evict entries to make space.
        
        Eviction strategy:
        1. Remove expired entries
        2. Remove least recently used entries
        """
        # Remove expired entries
        now = time.time()
        expired = [
            k for k, ttl in self._memory_ttl.items()
            if ttl < now
        ]
        for key in expired:
            self._remove_memory_entry(key)
        
        # If still need space, remove least used
        if len(self._memory_cache) >= self._max_items:
            # Sort by hits (least used first)
            sorted_entries = sorted(
                self._memory_hits.items(),
                key=lambda x: x[1]
            )
            
            # Remove bottom 10%
            to_remove = max(
                len(sorted_entries) // 10,
                1
            )
            for key, _ in sorted_entries[:to_remove]:
                self._remove_memory_entry(key)
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                # Sleep for 60 seconds
                time.sleep(60)
                
                # Perform cleanup
                with self._lock:
                    self._evict_entries()
                
            except Exception as e:
                self.logger.error(
                    f"Cleanup error: {str(e)}",
                    exc_info=True
                )
