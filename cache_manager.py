"""
Cache Manager for PyTrends API
Provides in-memory caching with optional Redis support
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from threading import Lock
import os

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Intelligent caching system with in-memory primary storage
    and optional Redis backend for distributed caching.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.redis_client = None
        
        # Try to connect to Redis if available
        self._init_redis()
        
        logger.info(f"CacheManager initialized with default TTL: {default_ttl}s")
        if self.redis_client:
            logger.info("Redis backend enabled")
        else:
            logger.info("Using in-memory cache only")
    
    def _init_redis(self):
        """Initialize Redis connection if available"""
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                import redis
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established")
        except ImportError:
            logger.warning("redis package not installed, using in-memory cache only")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory cache only")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a unique cache key from parameters
        
        Args:
            prefix: Cache key prefix (e.g., 'interest_over_time')
            **kwargs: Parameters to include in key
        
        Returns:
            Hashed cache key
        """
        # Sort kwargs for consistent keys
        sorted_params = sorted(kwargs.items())
        param_string = json.dumps(sorted_params, sort_keys=True)
        hash_suffix = hashlib.md5(param_string.encode()).hexdigest()[:12]
        return f"pytrends:{prefix}:{hash_suffix}"
    
    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            prefix: Cache key prefix
            **kwargs: Parameters used to generate key
        
        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(prefix, **kwargs)
        
        # Try Redis first if available
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis GET error: {e}")
        
        # Fallback to in-memory cache
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if expired
                if datetime.now() < entry['expires_at']:
                    logger.debug(f"Cache HIT (memory): {key}")
                    return entry['value']
                else:
                    # Remove expired entry
                    del self._cache[key]
                    logger.debug(f"Cache EXPIRED: {key}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, value: Any, prefix: str, ttl: Optional[int] = None, **kwargs):
        """
        Set cached value
        
        Args:
            value: Value to cache
            prefix: Cache key prefix
            ttl: Time-to-live in seconds (None = use default)
            **kwargs: Parameters used to generate key
        """
        key = self._generate_key(prefix, **kwargs)
        ttl = ttl or self.default_ttl
        
        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
                logger.debug(f"Cached to Redis: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.error(f"Redis SET error: {e}")
        
        # Always store in memory as backup
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now()
            }
            logger.debug(f"Cached to memory: {key} (TTL: {ttl}s)")
    
    def delete(self, prefix: str, **kwargs):
        """
        Delete cached value
        
        Args:
            prefix: Cache key prefix
            **kwargs: Parameters used to generate key
        """
        key = self._generate_key(prefix, **kwargs)
        
        # Delete from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis DELETE error: {e}")
        
        # Delete from memory
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted from cache: {key}")
    
    def clear_all(self):
        """Clear all cached values"""
        # Clear Redis
        if self.redis_client:
            try:
                # Delete only pytrends keys
                for key in self.redis_client.scan_iter("pytrends:*"):
                    self.redis_client.delete(key)
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.error(f"Redis CLEAR error: {e}")
        
        # Clear memory
        with self._lock:
            self._cache.clear()
            logger.info("Memory cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries from in-memory cache"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now >= entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            memory_count = len(self._cache)
            memory_expired = sum(
                1 for entry in self._cache.values()
                if datetime.now() >= entry['expires_at']
            )
        
        stats = {
            'memory': {
                'total_entries': memory_count,
                'expired_entries': memory_expired,
                'active_entries': memory_count - memory_expired
            },
            'redis': {
                'enabled': self.redis_client is not None,
                'connected': False
            }
        }
        
        # Get Redis stats if available
        if self.redis_client:
            try:
                self.redis_client.ping()
                stats['redis']['connected'] = True
                # Count pytrends keys
                count = sum(1 for _ in self.redis_client.scan_iter("pytrends:*"))
                stats['redis']['total_entries'] = count
            except Exception as e:
                logger.error(f"Redis STATS error: {e}")
        
        return stats


# Global cache instance
cache = CacheManager(default_ttl=3600)  # 1 hour default
