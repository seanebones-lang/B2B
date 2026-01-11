"""Retry utilities with exponential backoff"""

from typing import Callable, TypeVar, Optional, List
from functools import wraps
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Optional[tuple] = None
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exponential_base: Base for exponential backoff
        retryable_exceptions: Tuple of exception types to retry on
        
    Example:
        @retry_with_backoff(max_attempts=5, initial_wait=2.0)
        def unreliable_api_call():
            return make_request()
    """
    if retryable_exceptions is None:
        retryable_exceptions = (Exception,)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            "Max retry attempts reached",
                            function=func.__name__,
                            attempts=attempt,
                            error=str(e)
                        )
                        raise
                    
                    # Calculate wait time with exponential backoff
                    wait_time = min(
                        initial_wait * (exponential_base ** (attempt - 1)),
                        max_wait
                    )
                    
                    logger.warning(
                        "Retrying after error",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    
                    time.sleep(wait_time)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Unexpected retry failure")
        
        return wrapper
    return decorator


# Convenience decorators for common use cases
def retry_api_call(max_attempts: int = 3):
    """Retry decorator specifically for API calls"""
    return retry_with_backoff(
        max_attempts=max_attempts,
        initial_wait=2.0,
        max_wait=30.0,
        retryable_exceptions=(ConnectionError, TimeoutError, Exception)
    )


def retry_scraper(max_attempts: int = 3):
    """Retry decorator specifically for scraping operations"""
    return retry_with_backoff(
        max_attempts=max_attempts,
        initial_wait=3.0,
        max_wait=60.0,
        retryable_exceptions=(ConnectionError, TimeoutError, Exception)
    )
