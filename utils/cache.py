"""
Caching utilities for GitCanvas API
Implements TTL-based caching for GitHub API responses and SVG generation
Supports both local (TTLCache) and distributed (Redis) caching backends
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, Optional, Callable
from cachetools import TTLCache

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Cache configurations
GITHUB_API_CACHE_TTL = 5 * 60  # Keep live GitHub data reasonably fresh.
SVG_CACHE_TTL = 60 * 60  # 1 hour
CACHE_MAX_SIZE = 1000  # Maximum number of cached items

# Cache statistics
cache_stats = {
    'github_api': {'hits': 0, 'misses': 0},
    'svg': {'hits': 0, 'misses': 0}
}


# ==================== Cache Backend Implementations ====================

class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """Retrieve value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in cache with TTL"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class LocalCacheBackend(CacheBackend):
    """In-memory TTL cache backend for single-instance deployments"""
    
    def __init__(self, max_size: int = CACHE_MAX_SIZE):
        self.github_api_cache = TTLCache(maxsize=max_size, ttl=GITHUB_API_CACHE_TTL)
        self.svg_cache = TTLCache(maxsize=max_size, ttl=SVG_CACHE_TTL)
        self.max_size = max_size
    
    def get(self, key: str) -> Any:
        """Get value from appropriate cache based on key prefix"""
        cache = self._get_cache(key)
        if key in cache:
            return cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in appropriate cache"""
        cache = self._get_cache(key)
        cache[key] = value
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        cache = self._get_cache(key)
        return key in cache
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        cache = self._get_cache(key)
        if key in cache:
            del cache[key]
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear cache(s)"""
        if cache_type in (None, 'all'):
            self.github_api_cache.clear()
            self.svg_cache.clear()
        elif cache_type == 'github_api':
            self.github_api_cache.clear()
        elif cache_type == 'svg':
            self.svg_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'github_api': {
                'cache_size': len(self.github_api_cache),
                'max_size': self.max_size,
                'ttl': GITHUB_API_CACHE_TTL
            },
            'svg': {
                'cache_size': len(self.svg_cache),
                'max_size': self.max_size,
                'ttl': SVG_CACHE_TTL
            }
        }
    
    def _get_cache(self, key: str) -> TTLCache:
        """Route key to appropriate cache based on prefix"""
        if key.startswith('svg_'):
            return self.svg_cache
        return self.github_api_cache


class RedisCacheBackend(CacheBackend):
    """Distributed Redis cache backend for horizontal deployments"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", key_prefix: str = "gitcanvas:"):
        self.key_prefix = key_prefix if key_prefix.endswith(":") else f"{key_prefix}:"
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            self.connected = True
            logger.info(f"Redis cache backend connected to {redis_url} with prefix {self.key_prefix}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to local cache.")
            self.connected = False
            self.redis = None

    def _scoped_key(self, key: str) -> str:
        """Ensure all Redis keys are scoped to this application namespace."""
        if key.startswith(self.key_prefix):
            return key
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Any:
        """Retrieve from Redis"""
        if not self.connected or not self.redis:
            return None
        
        try:
            value = self.redis.get(self._scoped_key(key))
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store in Redis with TTL"""
        if not self.connected or not self.redis:
            return
        
        try:
            # Serialize value to JSON
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            self.redis.setex(self._scoped_key(key), ttl, serialized_value)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.connected or not self.redis:
            return False
        
        try:
            return self.redis.exists(self._scoped_key(key)) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> None:
        """Delete key from Redis"""
        if not self.connected or not self.redis:
            return
        
        try:
            self.redis.delete(self._scoped_key(key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear namespaced Redis cache with SCAN to avoid blocking."""
        if not self.connected or not self.redis:
            return
        
        try:
            if cache_type in (None, 'all'):
                key_suffix = "*"
            elif cache_type == 'svg':
                key_suffix = "svg_*"
            elif cache_type == 'github_api':
                key_suffix = "github_api_*"
            else:
                return

            pattern = f"{self.key_prefix}{key_suffix}"
            deleted_count = 0
            batch = []
            batch_size = 200

            for key in self.redis.scan_iter(match=pattern, count=1000):
                batch.append(key)
                if len(batch) >= batch_size:
                    deleted_count += self.redis.delete(*batch)
                    batch = []

            if batch:
                deleted_count += self.redis.delete(*batch)

            logger.info(f"Cleared {deleted_count} Redis keys in namespace with pattern {pattern}")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self.connected or not self.redis:
            return {'error': 'Redis not connected'}
        
        try:
            info = self.redis.info('memory')
            namespaced_keys = sum(1 for _ in self.redis.scan_iter(match=f"{self.key_prefix}*", count=1000))
            return {
                'connected': True,
                'memory_used_mb': info.get('used_memory_human', 'N/A'),
                'memory_peak_mb': info.get('used_memory_peak_human', 'N/A'),
                'total_keys': namespaced_keys,
                'key_prefix': self.key_prefix,
                'ttl_github_api': GITHUB_API_CACHE_TTL,
                'ttl_svg': SVG_CACHE_TTL
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {'error': str(e)}


# ==================== Cache Manager ====================

class CacheManager:
    """Manages cache backend with optional fallback"""
    
    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend or LocalCacheBackend()
        self.fallback = LocalCacheBackend()  # Always have local fallback
    
    def get(self, key: str) -> Any:
        """Get from primary backend, fallback to local if needed"""
        try:
            value = self.backend.get(key)
            if value is not None:
                return value
        except Exception as e:
            logger.warning(f"Primary cache get failed: {e}, using fallback")
        
        # Try fallback
        try:
            return self.fallback.get(key)
        except Exception as e:
            logger.error(f"Fallback cache get failed: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set in both primary and fallback backends"""
        try:
            self.backend.set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Primary cache set failed: {e}")
        
        try:
            self.fallback.set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Fallback cache set failed: {e}")
    
    def exists(self, key: str) -> bool:
        """Check in primary backend first, then fallback"""
        try:
            if self.backend.exists(key):
                return True
        except Exception as e:
            logger.warning(f"Primary cache exists check failed: {e}")
        
        try:
            return self.fallback.exists(key)
        except Exception as e:
            logger.error(f"Fallback cache exists check failed: {e}")
            return False
    
    def delete(self, key: str) -> None:
        """Delete from both backends"""
        try:
            self.backend.delete(key)
        except Exception as e:
            logger.warning(f"Primary cache delete failed: {e}")
        
        try:
            self.fallback.delete(key)
        except Exception as e:
            logger.warning(f"Fallback cache delete failed: {e}")
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear both backends"""
        try:
            self.backend.clear(cache_type)
        except Exception as e:
            logger.warning(f"Primary cache clear failed: {e}")
        
        try:
            self.fallback.clear(cache_type)
        except Exception as e:
            logger.warning(f"Fallback cache clear failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from primary backend"""
        try:
            return self.backend.get_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}


# ==================== Initialize Cache Manager ====================

def _init_cache_manager() -> CacheManager:
    """Initialize cache manager based on configuration"""
    try:
        from config.settings import GitCanvasSettings
        settings = GitCanvasSettings()
        
        if settings.redis_enabled and settings.redis_url:
            logger.info("Initializing Redis cache backend")
            redis_backend = RedisCacheBackend(settings.redis_url, settings.redis_key_prefix)
            if redis_backend.connected:
                return CacheManager(backend=redis_backend)
            else:
                logger.info("Redis connection failed, using local cache")
                return CacheManager(backend=LocalCacheBackend())
        else:
            logger.info("Using local cache backend")
            return CacheManager(backend=LocalCacheBackend())
    except Exception as e:
        logger.warning(f"Failed to initialize cache from settings: {e}. Using local cache.")
        return CacheManager(backend=LocalCacheBackend())


# Global cache manager instance
cache_manager = _init_cache_manager()


# ==================== Decorators ====================

def cache_github_api(func: Callable) -> Callable:
    """
    Decorator to cache GitHub API responses
    Supports both local and distributed Redis caching
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = f"github_api_{_create_cache_key(func.__name__, *args, **kwargs)}"
        
        # Check if result is in cache
        if cache_manager.exists(cache_key):
            cache_stats['github_api']['hits'] += 1
            return cache_manager.get(cache_key)
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        if result is not None:  # Only cache successful results
            cache_manager.set(cache_key, result, GITHUB_API_CACHE_TTL)
        
        cache_stats['github_api']['misses'] += 1
        return result
    
    return wrapper


def cache_svg_response(func: Callable) -> Callable:
    """
    Decorator to cache SVG generation responses
    Supports both local and distributed Redis caching
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = f"svg_{_create_cache_key(func.__name__, *args, **kwargs)}"
        
        # Check if result is in cache
        if cache_manager.exists(cache_key):
            cache_stats['svg']['hits'] += 1
            return cache_manager.get(cache_key)
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        if result is not None:  # Only cache successful results
            cache_manager.set(cache_key, result, SVG_CACHE_TTL)
        
        cache_stats['svg']['misses'] += 1
        return result
    
    return wrapper


def _create_cache_key(*args, **kwargs) -> str:
    """
    Create a unique cache key from function arguments
    """
    # Convert all arguments to string and create hash
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics including hit rates and cache backend info
    """
    backend_stats = cache_manager.get_stats()
    
    return {
        'backend': type(cache_manager.backend).__name__,
        'github_api': {
            'hits': cache_stats['github_api']['hits'],
            'misses': cache_stats['github_api']['misses'],
            'hit_rate': _calculate_hit_rate('github_api'),
            'ttl': GITHUB_API_CACHE_TTL
        },
        'svg': {
            'hits': cache_stats['svg']['hits'],
            'misses': cache_stats['svg']['misses'],
            'hit_rate': _calculate_hit_rate('svg'),
            'ttl': SVG_CACHE_TTL
        },
        'backend_stats': backend_stats
    }


def _calculate_hit_rate(cache_type: str) -> float:
    """
    Calculate cache hit rate as percentage
    """
    hits = cache_stats[cache_type]['hits']
    misses = cache_stats[cache_type]['misses']
    total = hits + misses
    
    if total == 0:
        return 0.0
    
    return round((hits / total) * 100, 2)


def clear_cache(cache_type: Optional[str] = None) -> Dict[str, str]:
    """
    Clear cache(s) in all configured backends
    
    Args:
        cache_type: 'github_api', 'svg', or None for all caches
    
    Returns:
        Status message
    """
    cache_manager.clear(cache_type)
    
    if cache_type == 'github_api':
        return {'status': 'GitHub API cache cleared'}
    elif cache_type == 'svg':
        return {'status': 'SVG cache cleared'}
    else:
        return {'status': 'All caches cleared'}