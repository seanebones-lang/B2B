"""Performance monitoring and metrics collection"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict
from datetime import datetime

from utils.logging import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, float] = {}
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a metric value
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for filtering
        """
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {}
        })
        logger.debug("Metric recorded", metric=name, value=value, tags=tags)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter
        
        Args:
            name: Counter name
            value: Increment value
            tags: Optional tags
        """
        self.counters[name] += value
        logger.debug("Counter incremented", counter=name, value=value, tags=tags)
    
    def start_timer(self, name: str) -> str:
        """
        Start a timer
        
        Args:
            name: Timer name
            
        Returns:
            Timer ID
        """
        timer_id = f"{name}_{time.time()}"
        self.timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str) -> float:
        """
        Stop a timer and record duration
        
        Args:
            timer_id: Timer ID from start_timer
            
        Returns:
            Duration in seconds
        """
        if timer_id not in self.timers:
            logger.warning("Timer not found", timer_id=timer_id)
            return 0.0
        
        duration = time.time() - self.timers[timer_id]
        del self.timers[timer_id]
        
        # Extract metric name from timer_id
        metric_name = timer_id.rsplit("_", 1)[0]
        self.record_metric(f"{metric_name}_duration", duration)
        
        return duration
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Returns:
            Dictionary with performance stats
        """
        stats = {
            "counters": dict(self.counters),
            "metrics": {}
        }
        
        for metric_name, values in self.metrics.items():
            if values:
                metric_values = [v["value"] for v in values]
                stats["metrics"][metric_name] = {
                    "count": len(metric_values),
                    "min": min(metric_values),
                    "max": max(metric_values),
                    "avg": sum(metric_values) / len(metric_values),
                    "p95": self._percentile(metric_values, 0.95),
                    "p99": self._percentile(metric_values, 0.99)
                }
        
        return stats
    
    def _percentile(self, values: list, percentile: float) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.counters.clear()
        self.timers.clear()


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def monitor_performance(metric_name: str):
    """
    Decorator to monitor function performance
    
    Args:
        metric_name: Name of the metric to record
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_monitor()
            timer_id = monitor.start_timer(metric_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = monitor.stop_timer(timer_id)
                logger.info(
                    "Function execution time",
                    function=func.__name__,
                    duration=duration,
                    metric=metric_name
                )
        return wrapper
    return decorator


async def monitor_performance_async(metric_name: str):
    """
    Decorator to monitor async function performance
    
    Args:
        metric_name: Name of the metric to record
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_monitor()
            timer_id = monitor.start_timer(metric_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = monitor.stop_timer(timer_id)
                logger.info(
                    "Async function execution time",
                    function=func.__name__,
                    duration=duration,
                    metric=metric_name
                )
        return wrapper
    return decorator
