"""Circuit breaker implementation for fault tolerance"""

import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta

from utils.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit
            expected_exception: Exception type to catch
            name: Name of circuit breaker for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        self.half_open_success_threshold = 2  # Need 2 successes to close
        
        logger.info(
            "Circuit breaker initialized",
            name=self.name,
            failure_threshold=self.failure_threshold,
            timeout=self.timeout
        )
    
    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state", name=self.name)
            else:
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable. Last failure: {self.last_failure_time}"
                )
        
        # Attempt function call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout
    
    def _on_success(self) -> None:
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                "Half-open success",
                name=self.name,
                success_count=self.success_count
            )
            
            if self.success_count >= self.half_open_success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker CLOSED - service recovered", name=self.name)
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
                logger.debug("Failure count reset", name=self.name)
    
    def _on_failure(self) -> None:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            "Circuit breaker failure",
            name=self.name,
            failure_count=self.failure_count,
            state=self.state.value
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during half-open, go back to open
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning("Circuit breaker OPEN - service still failing", name=self.name)
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    "Circuit breaker OPEN - threshold exceeded",
                    name=self.name,
                    failure_count=self.failure_count,
                    threshold=self.failure_threshold
                )
    
    def reset(self) -> None:
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset", name=self.name)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout
        }


# Global circuit breaker instances
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type = Exception
) -> CircuitBreaker:
    """
    Get or create circuit breaker instance
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failure threshold
        timeout: Timeout in seconds
        expected_exception: Exception type to catch
        
    Returns:
        Circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
            name=name
        )
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorator for circuit breaker protection
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failure threshold
        timeout: Timeout in seconds
        expected_exception: Exception type to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        breaker = get_circuit_breaker(name, failure_threshold, timeout, expected_exception)
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator
