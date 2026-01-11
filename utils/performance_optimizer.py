"""Performance optimization utilities based on monitoring data"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

from utils.monitoring import get_monitoring
from utils.logging import get_logger

logger = get_logger(__name__)


class PerformanceOptimizer:
    """Performance optimization based on monitoring data"""
    
    def __init__(self):
        self.monitor = get_monitoring()
        self.optimization_suggestions = []
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze performance metrics and identify bottlenecks
        
        Returns:
            Dictionary with performance analysis and suggestions
        """
        stats = self.monitor.get_stats()
        analysis = {
            "metrics": stats,
            "bottlenecks": [],
            "suggestions": [],
            "optimization_score": 0
        }
        
        # Analyze metrics for bottlenecks
        if "metrics" in stats:
            for metric_name, metric_data in stats["metrics"].items():
                # Identify slow operations (>1 second average)
                if metric_data.get("avg", 0) > 1.0:
                    analysis["bottlenecks"].append({
                        "metric": metric_name,
                        "avg_duration": metric_data["avg"],
                        "p95_duration": metric_data.get("p95", 0),
                        "count": metric_data.get("count", 0)
                    })
                    
                    # Generate suggestions
                    if "scraping" in metric_name.lower():
                        analysis["suggestions"].append({
                            "type": "caching",
                            "metric": metric_name,
                            "suggestion": "Consider increasing cache TTL for scraped reviews"
                        })
                    elif "database" in metric_name.lower():
                        analysis["suggestions"].append({
                            "type": "database",
                            "metric": metric_name,
                            "suggestion": "Consider adding database indexes or connection pooling"
                        })
                    elif "api" in metric_name.lower():
                        analysis["suggestions"].append({
                            "type": "api",
                            "metric": metric_name,
                            "suggestion": "Consider batching API requests or using async operations"
                        })
        
        # Calculate optimization score (0-100)
        if analysis["bottlenecks"]:
            # Lower score if there are bottlenecks
            analysis["optimization_score"] = max(0, 100 - len(analysis["bottlenecks"]) * 10)
        else:
            analysis["optimization_score"] = 100
        
        return analysis
    
    def get_cache_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get cache optimization recommendations
        
        Returns:
            List of cache recommendations
        """
        stats = self.monitor.get_stats()
        recommendations = []
        
        # Check cache hit rates (if tracked)
        cache_misses = self.monitor.counters.get("cache_misses", 0)
        cache_hits = self.monitor.counters.get("cache_hits", 0)
        
        if cache_misses + cache_hits > 0:
            hit_rate = cache_hits / (cache_hits + cache_misses)
            
            if hit_rate < 0.5:
                recommendations.append({
                    "type": "cache_ttl",
                    "priority": "high",
                    "suggestion": "Cache hit rate is low. Consider increasing cache TTL or cache size."
                })
        
        return recommendations
    
    def get_database_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get database optimization recommendations
        
        Returns:
            List of database recommendations
        """
        recommendations = []
        stats = self.monitor.get_stats()
        
        # Check for slow database queries
        db_metrics = {
            k: v for k, v in stats.get("metrics", {}).items()
            if "database" in k.lower() or "db" in k.lower()
        }
        
        for metric_name, metric_data in db_metrics.items():
            if metric_data.get("avg", 0) > 0.1:  # >100ms
                recommendations.append({
                    "type": "database_index",
                    "priority": "medium",
                    "suggestion": f"Consider adding indexes for {metric_name} queries"
                })
        
        return recommendations
    
    def optimize_batch_size(self, current_batch_size: int, avg_duration: float) -> int:
        """
        Optimize batch size based on performance
        
        Args:
            current_batch_size: Current batch size
            avg_duration: Average duration per batch
            
        Returns:
            Optimized batch size
        """
        # If batches are too fast, increase size
        if avg_duration < 0.1:
            return min(current_batch_size * 2, 100)
        
        # If batches are too slow, decrease size
        if avg_duration > 1.0:
            return max(current_batch_size // 2, 1)
        
        return current_batch_size
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """
        Get comprehensive optimization report
        
        Returns:
            Dictionary with optimization report
        """
        performance_analysis = self.analyze_performance()
        cache_recommendations = self.get_cache_recommendations()
        db_recommendations = self.get_database_recommendations()
        
        return {
            "performance_analysis": performance_analysis,
            "cache_recommendations": cache_recommendations,
            "database_recommendations": db_recommendations,
            "overall_score": performance_analysis["optimization_score"],
            "total_recommendations": len(cache_recommendations) + len(db_recommendations)
        }


# Global optimizer instance
_optimizer: Optional[PerformanceOptimizer] = None


def get_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer
