#!/usr/bin/env python3
"""
FAME Production Cache Manager
Stores last-known-good data for degraded mode fallback
Production-grade caching with TTL and deterministic fallback
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Try Redis for production, fallback to in-memory
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProductionCacheManager:
    """
    Production cache manager for degraded mode
    Stores last-known-good data with timestamps
    """
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        """
        Initialize cache manager
        
        Args:
            redis_url: Redis connection URL (optional, uses in-memory if not provided)
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.default_ttl = default_ttl
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory cache: {e}")
                self.redis_client = None
        else:
            logger.info("Using in-memory cache (Redis not configured)")
    
    def get(self, key: str, max_age_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached data if fresh
        
        Args:
            key: Cache key
            max_age_seconds: Maximum age in seconds (default: uses default_ttl)
            
        Returns:
            Cached data dict if fresh, None otherwise
        """
        try:
            max_age = max_age_seconds if max_age_seconds is not None else self.default_ttl
            
            if self.redis_client:
                # Try Redis first
                try:
                    data = self.redis_client.get(key)
                    if data:
                        import json
                        cached_entry = json.loads(data)
                        age = time.time() - cached_entry.get('timestamp', 0)
                        if age < max_age:
                            logger.debug(f"Cache HIT (Redis): {key}, age: {age:.1f}s")
                            return cached_entry.get('data')
                        else:
                            logger.debug(f"Cache EXPIRED (Redis): {key}, age: {age:.1f}s")
                            return None
                except Exception as e:
                    logger.warning(f"Redis get failed: {e}, trying memory cache")
            
            # Fallback to memory cache
            if key in self.memory_cache:
                cached_entry = self.memory_cache[key]
                age = time.time() - cached_entry.get('timestamp', 0)
                if age < max_age:
                    logger.debug(f"Cache HIT (Memory): {key}, age: {age:.1f}s")
                    return cached_entry.get('data')
                else:
                    logger.debug(f"Cache EXPIRED (Memory): {key}, age: {age:.1f}s")
                    del self.memory_cache[key]
                    return None
            
            logger.debug(f"Cache MISS: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store data in cache
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: TTL in seconds (default: uses default_ttl)
            
        Returns:
            True if stored, False otherwise
        """
        try:
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            cached_entry = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl_seconds
            }
            
            if self.redis_client:
                try:
                    import json
                    self.redis_client.setex(
                        key,
                        ttl_seconds,
                        json.dumps(cached_entry)
                    )
                    logger.debug(f"Cached (Redis): {key}, TTL: {ttl_seconds}s")
                    return True
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}, using memory cache")
            
            # Fallback to memory cache
            self.memory_cache[key] = cached_entry
            
            # Clean expired entries periodically
            if len(self.memory_cache) > 1000:
                self._clean_expired()
            
            logger.debug(f"Cached (Memory): {key}, TTL: {ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get_timestamp(self, key: str) -> Optional[float]:
        """Get timestamp of cached data"""
        try:
            if self.redis_client:
                try:
                    import json
                    data = self.redis_client.get(key)
                    if data:
                        cached_entry = json.loads(data)
                        return cached_entry.get('timestamp')
                except Exception:
                    pass
            
            if key in self.memory_cache:
                return self.memory_cache[key].get('timestamp')
            
            return None
        except Exception as e:
            logger.error(f"Cache timestamp error: {e}")
            return None
    
    def _clean_expired(self):
        """Clean expired entries from memory cache"""
        try:
            now = time.time()
            expired_keys = [
                k for k, v in self.memory_cache.items()
                if now - v.get('timestamp', 0) > v.get('ttl', self.default_ttl)
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            if expired_keys:
                logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
        except Exception as e:
            logger.error(f"Cache clean error: {e}")


# Global cache manager instance
_cache_manager: Optional[ProductionCacheManager] = None


def get_cache_manager() -> ProductionCacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        import os
        redis_url = os.getenv("FAME_REDIS_URL")
        default_ttl = int(os.getenv("FAME_CACHE_TTL", "300"))  # 5 minutes default
        _cache_manager = ProductionCacheManager(redis_url=redis_url, default_ttl=default_ttl)
    return _cache_manager


__all__ = ['ProductionCacheManager', 'get_cache_manager']

