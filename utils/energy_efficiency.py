"""Energy efficiency and sustainability utilities"""

import time
import psutil
import os
from typing import Dict, Any, Optional
from functools import wraps

from utils.logging import get_logger
from utils.monitoring import get_monitoring

logger = get_logger(__name__)
monitor = get_monitoring()


class EnergyEfficiencyTracker:
    """Track and optimize energy efficiency"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        logger.info("Energy efficiency tracker initialized")
    
    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage
        
        Returns:
            CPU usage percentage
        """
        return self.process.cpu_percent(interval=0.1)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage
        
        Returns:
            Dictionary with memory usage information
        """
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            "percent": self.process.memory_percent()
        }
    
    def estimate_energy_consumption(self, duration_seconds: float, cpu_usage: float) -> Dict[str, float]:
        """
        Estimate energy consumption for an operation
        
        Args:
            duration_seconds: Duration of operation in seconds
            cpu_usage: Average CPU usage percentage
            
        Returns:
            Dictionary with energy consumption estimates
        """
        # Rough estimation: 1W per 10% CPU usage per core
        # This is a simplified model - actual consumption varies by hardware
        cpu_cores = psutil.cpu_count()
        base_power_watts = 5.0  # Base system power
        cpu_power_watts = (cpu_usage / 100.0) * cpu_cores * 0.1  # 0.1W per % per core
        
        total_power_watts = base_power_watts + cpu_power_watts
        energy_joules = total_power_watts * duration_seconds
        energy_kwh = energy_joules / 3600000  # Convert to kWh
        
        # Estimate CO2 (assuming 0.5 kg CO2 per kWh - varies by region)
        co2_kg = energy_kwh * 0.5
        
        return {
            "energy_joules": energy_joules,
            "energy_kwh": energy_kwh,
            "co2_kg": co2_kg,
            "power_watts": total_power_watts,
            "duration_seconds": duration_seconds
        }
    
    def track_operation_energy(self, operation_name: str):
        """
        Decorator to track energy consumption of an operation
        
        Args:
            operation_name: Name of the operation
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_cpu = self.get_cpu_usage()
                
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                end_cpu = self.get_cpu_usage()
                avg_cpu = (start_cpu + end_cpu) / 2
                
                energy = self.estimate_energy_consumption(duration, avg_cpu)
                
                # Record metrics
                monitor.record_metric(f"{operation_name}_energy_kwh", energy["energy_kwh"])
                monitor.record_metric(f"{operation_name}_co2_kg", energy["co2_kg"])
                
                logger.info(
                    "Operation energy tracked",
                    operation=operation_name,
                    duration=duration,
                    energy_kwh=energy["energy_kwh"],
                    co2_kg=energy["co2_kg"]
                )
                
                return result
            return wrapper
        return decorator
    
    def get_efficiency_report(self) -> Dict[str, Any]:
        """
        Get energy efficiency report
        
        Returns:
            Dictionary with efficiency metrics
        """
        stats = monitor.get_stats()
        
        # Calculate total energy consumption
        total_energy_kwh = sum(
            metric_data.get("sum", 0) / 1000  # Convert from Wh to kWh
            for metric_name, metric_data in stats.get("metrics", {}).items()
            if "energy_kwh" in metric_name
        )
        
        total_co2_kg = sum(
            metric_data.get("sum", 0)
            for metric_name, metric_data in stats.get("metrics", {}).items()
            if "co2_kg" in metric_name
        )
        
        current_cpu = self.get_cpu_usage()
        current_memory = self.get_memory_usage()
        
        return {
            "total_energy_kwh": total_energy_kwh,
            "total_co2_kg": total_co2_kg,
            "current_cpu_percent": current_cpu,
            "current_memory_mb": current_memory["rss_mb"],
            "efficiency_score": self._calculate_efficiency_score(current_cpu, current_memory["percent"])
        }
    
    def _calculate_efficiency_score(self, cpu_percent: float, memory_percent: float) -> float:
        """
        Calculate energy efficiency score (0-1)
        
        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            
        Returns:
            Efficiency score (higher is better)
        """
        # Lower usage = higher efficiency
        cpu_score = max(0, 1 - (cpu_percent / 100))
        memory_score = max(0, 1 - (memory_percent / 100))
        
        return (cpu_score + memory_score) / 2
    
    def optimize_for_energy(self, operation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide recommendations for energy-efficient operation
        
        Args:
            operation_config: Operation configuration
            
        Returns:
            Dictionary with optimization recommendations
        """
        recommendations = []
        
        # Check batch size
        batch_size = operation_config.get("batch_size", 1)
        if batch_size < 10:
            recommendations.append({
                "type": "batch_size",
                "current": batch_size,
                "recommended": min(batch_size * 2, 50),
                "reason": "Larger batches reduce overhead and improve energy efficiency"
            })
        
        # Check caching
        use_cache = operation_config.get("use_cache", False)
        if not use_cache:
            recommendations.append({
                "type": "caching",
                "recommended": True,
                "reason": "Caching reduces redundant computations and saves energy"
            })
        
        # Check async operations
        use_async = operation_config.get("use_async", False)
        if not use_async:
            recommendations.append({
                "type": "async",
                "recommended": True,
                "reason": "Async operations improve CPU utilization and reduce idle time"
            })
        
        return {
            "recommendations": recommendations,
            "potential_savings_percent": len(recommendations) * 10  # Rough estimate
        }


# Global instance
_energy_tracker: Optional[EnergyEfficiencyTracker] = None


def get_energy_tracker() -> EnergyEfficiencyTracker:
    """Get global energy efficiency tracker instance"""
    global _energy_tracker
    if _energy_tracker is None:
        _energy_tracker = EnergyEfficiencyTracker()
    return _energy_tracker
