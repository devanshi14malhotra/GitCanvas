"""
Caching utilities for GitCanvas API
Implements TTL-based caching for GitHub API responses and SVG generation
"""

import hashlib
import time
from functools import wraps
from typing import Any, Dict, Optional, Callable
from cachetools import TTLCache

# Cache configurations
GITHUB_API_CACHE_TTL = 15 * 60  # 15 minutes
SVG_CACHE_TTL = 60 * 60  # 1 hour
CACHE_MAX_SIZE = 1000  # Maximum number of cached items

# Initialize caches
github_api_cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=GITHUB_API_CACHE_TTL)
svg_cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=SVG_CACHE_TTL)

# Cache statistics
cache_stats = {
    'github_api': {'hits': 0, 'misses': 0},
    'svg': {'hits': 0, 'misses': 0}
}


def cache_github_api(func: Callable) -> Callable:
    """
    Decorator to cache GitHub API responses
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = _create_cache_key(func.__name__, *args, **kwargs)
        
        # Check if result is in cache
        if cache_key in github_api_cache:
            cache_stats['github_api']['hits'] += 1
            return github_api_cache[cache_key]
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        if result is not None:  # Only cache successful results
            github_api_cache[cache_key] = result
        
        cache_stats['github_api']['misses'] += 1
        return result
    
    return wrapper


def cache_svg_response(func: Callable) -> Callable:
    """
    Decorator to cache SVG generation responses
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = _create_cache_key(func.__name__, *args, **kwargs)
        
        # Check if result is in cache
        if cache_key in svg_cache:
            cache_stats['svg']['hits'] += 1
            return svg_cache[cache_key]
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        if result is not None:  # Only cache successful results
            svg_cache[cache_key] = result
        
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
    Get cache statistics including hit rates and cache sizes
    """
    return {
        'github_api': {
            'hits': cache_stats['github_api']['hits'],
            'misses': cache_stats['github_api']['misses'],
            'hit_rate': _calculate_hit_rate('github_api'),
            'cache_size': len(github_api_cache),
            'max_size': github_api_cache.maxsize,
            'ttl': GITHUB_API_CACHE_TTL
        },
        'svg': {
            'hits': cache_stats['svg']['hits'],
            'misses': cache_stats['svg']['misses'],
            'hit_rate': _calculate_hit_rate('svg'),
            'cache_size': len(svg_cache),
            'max_size': svg_cache.maxsize,
            'ttl': SVG_CACHE_TTL
        }
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
    Clear cache(s)
    
    Args:
        cache_type: 'github_api', 'svg', or None for all caches
    
    Returns:
        Status message
    """
    if cache_type == 'github_api':
        github_api_cache.clear()
        return {'status': 'GitHub API cache cleared'}
    elif cache_type == 'svg':
        svg_cache.clear()
        return {'status': 'SVG cache cleared'}
    else:
        github_api_cache.clear()
        svg_cache.clear()
        return {'status': 'All caches cleared'}