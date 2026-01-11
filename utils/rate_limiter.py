"""Rate limiting utilities"""

import time
from collections import defaultdict
from typing import Dict, Optional
from datetime import datetime, timedelta
import os


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(
        self,
        requests_per_minute: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per minute
            enabled: Whether rate limiting is enabled
        """
        self.enabled = (
            enabled if enabled is not None
            else os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        )
        self.requests_per_minute = (
            requests_per_minute if requests_per_minute is not None
            else int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        )
        
        # Store request timestamps per identifier (e.g., IP, user_id)
        self._requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str = "default") -> bool:
        """
        Check if request is allowed under rate limit
        
        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            
        Returns:
            True if allowed, False if rate limited
        """
        if not self.enabled:
            return True
        
        now = time.time()
        cutoff = now - 60  # Last minute
        
        # Clean old requests
        self._requests[identifier] = [
            ts for ts in self._requests[identifier] if ts > cutoff
        ]
        
        # Check limit
        if len(self._requests[identifier]) >= self.requests_per_minute:
            return False
        
        # Record request
        self._requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str = "default") -> int:
        """
        Get remaining requests in current window
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        if not self.enabled:
            return self.requests_per_minute
        
        now = time.time()
        cutoff = now - 60
        
        self._requests[identifier] = [
            ts for ts in self._requests[identifier] if ts > cutoff
        ]
        
        return max(0, self.requests_per_minute - len(self._requests[identifier]))
    
    def reset(self, identifier: Optional[str] = None) -> None:
        """
        Reset rate limit for identifier or all
        
        Args:
            identifier: Identifier to reset, or None for all
        """
        if identifier:
            self._requests.pop(identifier, None)
        else:
            self._requests.clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(requests_per_minute: Optional[int] = None):
    """
    Decorator to rate limit function calls
    
    Args:
        requests_per_minute: Requests per minute limit
        
    Example:
        @rate_limit(requests_per_minute=10)
        def api_call():
            return make_api_request()
    """
    limiter = RateLimiter(requests_per_minute=requests_per_minute)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            identifier = kwargs.get("user_id", "default")
            if not limiter.is_allowed(identifier):
                raise RuntimeError(
                    f"Rate limit exceeded. "
                    f"Limit: {limiter.requests_per_minute} requests/minute"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
