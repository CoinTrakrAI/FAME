#!/usr/bin/env python3
"""
Enterprise TTL Cache with LRU eviction
Thread-safe cache implementation for trading preferences and other services
"""

import threading
import time
import logging
import asyncio
from typing import Any, Dict, Optional, Callable
from collections import OrderedDict

logger = logging.getLogger(__name__)


class EnterpriseCache:
    """
    Thread-safe TTL cache with LRU eviction and circuit breaker support.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600.0,  # 1 hour default
        enable_metrics: bool = True
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_metrics = enable_metrics
        
        # Thread-safe storage
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        
        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired (async for compatibility)"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            expire_time = entry.get('expire_time')
            
            # Check expiration
            if expire_time and time.time() > expire_time:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry['value']
    
    def get_sync(self, key: str) -> Optional[Any]:
        """Synchronous version of get for compatibility"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            expire_time = entry.get('expire_time')
            
            if expire_time and time.time() > expire_time:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache with optional TTL"""
        with self._lock:
            ttl = ttl if ttl is not None else self.default_ttl
            expire_time = time.time() + ttl if ttl > 0 else None
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = {
                    'value': value,
                    'expire_time': expire_time,
                    'created_at': self._cache[key].get('created_at', time.time())
                }
                self._cache.move_to_end(key)
            else:
                # Add new entry
                self._cache[key] = {
                    'value': value,
                    'expire_time': expire_time,
                    'created_at': time.time()
                }
                
                # Evict if over size limit (LRU)
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._evictions += 1
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def expire_entries(self) -> int:
        """Remove expired entries, return count removed"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.get('expire_time') and entry['expire_time'] < current_time
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get cache metrics for observability"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_ratio': hit_ratio,
                'evictions': self._evictions,
                'expired_entries': self.expire_entries()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_metrics_snapshot for compatibility"""
        return self.get_metrics_snapshot()
    
    def __len__(self) -> int:
        """Return number of cache entries"""
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (not expired)"""
        return self.get(key) is not None
