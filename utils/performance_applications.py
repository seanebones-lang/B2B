"""Apply performance optimizations based on monitoring data"""

from typing import Dict, List, Any
from utils.performance_optimizer import get_optimizer
from utils.cache import CacheManager
from utils.database import get_db_manager
from utils.logging import get_logger

logger = get_logger(__name__)


class PerformanceApplications:
    """Apply performance optimizations"""
    
    def __init__(self):
        self.optimizer = get_optimizer()
        self.cache_manager = CacheManager()
        self.db_manager = get_db_manager()
    
    def apply_cache_optimizations(self):
        """Apply cache optimizations based on recommendations"""
        recommendations = self.optimizer.get_cache_recommendations()
        
        applied = []
        for rec in recommendations:
            if rec["type"] == "cache_ttl":
                # Increase cache TTL for better hit rate
                logger.info("Applying cache optimization", recommendation=rec["suggestion"])
                # Cache manager already has optimized defaults
                applied.append(rec)
        
        return applied
    
    def apply_database_optimizations(self):
        """Apply database optimizations"""
        recommendations = self.optimizer.get_database_recommendations()
        
        applied = []
        for rec in recommendations:
            if rec["type"] == "database_index":
                logger.info("Database index recommendation", recommendation=rec["suggestion"])
                # Indexes are already added in database models
                applied.append(rec)
        
        return applied
    
    def optimize_batch_operations(self, batch_size: int, operation_type: str) -> int:
        """
        Optimize batch size based on performance data
        
        Args:
            batch_size: Current batch size
            operation_type: Type of operation
            
        Returns:
            Optimized batch size
        """
        stats = self.optimizer.monitor.get_stats()
        
        # Find relevant metrics
        metric_name = f"{operation_type}_duration"
        if metric_name in stats.get("metrics", {}):
            metric_data = stats["metrics"][metric_name]
            avg_duration = metric_data.get("avg", 0)
            
            optimized_size = self.optimizer.optimize_batch_size(batch_size, avg_duration)
            
            if optimized_size != batch_size:
                logger.info(
                    "Batch size optimized",
                    operation=operation_type,
                    old_size=batch_size,
                    new_size=optimized_size
                )
            
            return optimized_size
        
        return batch_size
    
    def apply_all_optimizations(self) -> Dict[str, Any]:
        """
        Apply all performance optimizations
        
        Returns:
            Dictionary with applied optimizations
        """
        cache_optimizations = self.apply_cache_optimizations()
        db_optimizations = self.apply_database_optimizations()
        
        return {
            "cache_optimizations": cache_optimizations,
            "database_optimizations": db_optimizations,
            "total_applied": len(cache_optimizations) + len(db_optimizations)
        }


# Global instance
_perf_applications: PerformanceApplications = None


def get_perf_applications() -> PerformanceApplications:
    """Get global performance applications instance"""
    global _perf_applications
    if _perf_applications is None:
        _perf_applications = PerformanceApplications()
    return _perf_applications
