"""
GitHub API Rate Limiting Module

This module provides comprehensive rate limiting, retry logic, and backoff strategies
for GitHub API requests to prevent failures and improve reliability.
"""

import time
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimitInfo:
    """Container for GitHub API rate limit information"""
    
    def __init__(self, remaining: int = 0, limit: int = 0, reset_time: int = 0, used: int = 0):
        self.remaining = remaining
        self.limit = limit
        self.reset_time = reset_time
        self.used = used
        self.reset_datetime = datetime.fromtimestamp(reset_time) if reset_time else None
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> 'RateLimitInfo':
        """Create RateLimitInfo from response headers"""
        return cls(
            remaining=int(headers.get('X-RateLimit-Remaining', 0)),
            limit=int(headers.get('X-RateLimit-Limit', 0)),
            reset_time=int(headers.get('X-RateLimit-Reset', 0)),
            used=int(headers.get('X-RateLimit-Used', 0))
        )
    
    def time_until_reset(self) -> float:
        """Get seconds until rate limit resets"""
        if not self.reset_time:
            return 0
        return max(0, self.reset_time - time.time())
    
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted"""
        return self.remaining <= 0
    
    def should_wait(self, threshold: int = 5) -> bool:
        """Check if we should wait before making more requests"""
        return self.remaining <= threshold
    
    def __str__(self) -> str:
        return f"RateLimit(remaining={self.remaining}, limit={self.limit}, resets_in={self.time_until_reset():.1f}s)"


class GitHubRateLimiter:
    """GitHub API rate limiter with exponential backoff and intelligent retry logic"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 300.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.last_rate_limit_info: Optional[RateLimitInfo] = None
        self.request_count = 0
        
    def make_request(self, url: str, headers: Optional[Dict[str, str]] = None, 
                    timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """
        Make a GitHub API request with comprehensive rate limiting and retry logic
        
        Args:
            url: The API endpoint URL
            headers: Request headers
            timeout: Request timeout in seconds
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            Response object or None if all retries failed
        """
        headers = headers or {}
        self.request_count += 1
        
        for attempt in range(self.max_retries + 1):
            try:
                # Check if we should wait before making the request
                if self.last_rate_limit_info and self.last_rate_limit_info.should_wait():
                    wait_time = min(self.last_rate_limit_info.time_until_reset(), self.max_delay)
                    if wait_time > 0:
                        logger.warning(f"Rate limit threshold reached. Waiting {wait_time:.1f}s before request")
                        time.sleep(wait_time)
                
                # Make the request
                logger.debug(f"Making GitHub API request (attempt {attempt + 1}/{self.max_retries + 1}): {url}")
                response = requests.get(url, headers=headers, timeout=timeout, **kwargs)
                
                # Extract rate limit information
                rate_limit = RateLimitInfo.from_headers(response.headers)
                self.last_rate_limit_info = rate_limit
                
                # Log rate limit status
                logger.debug(f"Rate limit status: {rate_limit}")
                
                # Handle different response codes
                if response.status_code == 200:
                    logger.debug(f"Request successful: {url}")
                    return response
                
                elif response.status_code == 429:  # Rate limited
                    wait_time = rate_limit.time_until_reset()
                    if wait_time > self.max_delay:
                        logger.error(f"Rate limit reset time too long ({wait_time:.1f}s), giving up")
                        return None
                    
                    if attempt < self.max_retries:
                        logger.warning(f"Rate limited (429). Waiting {wait_time:.1f}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limited and max retries exceeded for: {url}")
                        return None
                
                elif response.status_code == 403:
                    # Check if it's a rate limit issue (GitHub sometimes returns 403 for rate limits)
                    if rate_limit.is_exhausted():
                        wait_time = rate_limit.time_until_reset()
                        if wait_time <= self.max_delay and attempt < self.max_retries:
                            logger.warning(f"Rate limited (403). Waiting {wait_time:.1f}s before retry {attempt + 1}")
                            time.sleep(wait_time)
                            continue
                    
                    logger.error(f"Forbidden (403) - possibly authentication issue: {url}")
                    return None
                
                elif response.status_code in [500, 502, 503, 504]:  # Server errors
                    if attempt < self.max_retries:
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        logger.warning(f"Server error ({response.status_code}). Retrying in {delay:.1f}s")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Server error ({response.status_code}) and max retries exceeded: {url}")
                        return None
                
                else:
                    # Other client errors (400, 401, 404, etc.) - don't retry
                    logger.error(f"Client error ({response.status_code}): {url}")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Request timeout. Retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Request timeout and max retries exceeded: {url}")
                    return None
                    
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Connection error. Retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Connection error and max retries exceeded: {url}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error making request to {url}: {e}")
                return None
        
        return None
    
    def get_rate_limit_status(self) -> Optional[RateLimitInfo]:
        """Get the last known rate limit status"""
        return self.last_rate_limit_info
    
    def estimate_requests_remaining(self) -> int:
        """Estimate how many requests can be made before hitting rate limit"""
        if not self.last_rate_limit_info:
            return 0
        return self.last_rate_limit_info.remaining
    
    def time_until_reset(self) -> float:
        """Get time until rate limit resets"""
        if not self.last_rate_limit_info:
            return 0
        return self.last_rate_limit_info.time_until_reset()


# Global rate limiter instance
_github_rate_limiter = GitHubRateLimiter()


def make_github_request(url: str, headers: Optional[Dict[str, str]] = None, 
                       timeout: int = 10, **kwargs) -> Optional[requests.Response]:
    """
    Convenience function to make a GitHub API request with rate limiting
    
    Args:
        url: The API endpoint URL
        headers: Request headers
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for requests.get()
        
    Returns:
        Response object or None if request failed
    """
    return _github_rate_limiter.make_request(url, headers, timeout, **kwargs)


def get_rate_limit_status() -> Optional[RateLimitInfo]:
    """Get the current rate limit status"""
    return _github_rate_limiter.get_rate_limit_status()


def check_rate_limit_before_requests(num_requests: int = 1) -> Tuple[bool, str]:
    """
    Check if we can make the specified number of requests without hitting rate limits
    
    Args:
        num_requests: Number of requests we want to make
        
    Returns:
        Tuple of (can_proceed, message)
    """
    rate_limit = get_rate_limit_status()
    
    if not rate_limit:
        return True, "No rate limit information available"
    
    if rate_limit.remaining >= num_requests:
        return True, f"Can make {num_requests} requests ({rate_limit.remaining} remaining)"
    
    wait_time = rate_limit.time_until_reset()
    return False, f"Rate limit exceeded. Need to wait {wait_time:.1f}s for reset"


def log_rate_limit_summary():
    """Log a summary of current rate limit status"""
    rate_limit = get_rate_limit_status()
    if rate_limit:
        logger.info(f"GitHub API Rate Limit Summary: {rate_limit}")
        logger.info(f"Total requests made this session: {_github_rate_limiter.request_count}")
    else:
        logger.info("No rate limit information available")