"""Health check utilities for monitoring system status"""

from typing import Dict, Any, Optional
from datetime import datetime
import os

from utils.database import get_db_manager
from utils.logging import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """System health checker"""
    
    def __init__(self):
        self.db_manager = None
        try:
            self.db_manager = get_db_manager()
        except Exception as e:
            logger.warning("Database manager not available", error=str(e))
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            Dictionary with health status and details
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check database
        db_check = self._check_database()
        health_status["checks"]["database"] = db_check
        
        # Check environment
        env_check = self._check_environment()
        health_status["checks"]["environment"] = env_check
        
        # Check dependencies
        deps_check = self._check_dependencies()
        health_status["checks"]["dependencies"] = deps_check
        
        # Overall status
        all_healthy = all(
            check.get("status") == "healthy"
            for check in health_status["checks"].values()
        )
        
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            if not self.db_manager:
                return {
                    "status": "unavailable",
                    "message": "Database manager not initialized"
                }
            
            # Try to get a session
            session = self.db_manager.get_session()
            session.close()
            
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
    
    def _check_environment(self) -> Dict[str, Any]:
        """Check environment configuration"""
        required_vars = ["XAI_API_KEY"]  # Optional but should be set
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var) and not os.getenv(var, "").strip():
                missing_vars.append(var)
        
        if missing_vars:
            return {
                "status": "degraded",
                "message": f"Missing optional environment variables: {', '.join(missing_vars)}"
            }
        
        return {
            "status": "healthy",
            "message": "Environment configuration OK"
        }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies"""
        dependencies = {
            "sentence_transformers": False,
            "sklearn": False,
            "openai": False,
            "streamlit": False
        }
        
        try:
            import sentence_transformers
            dependencies["sentence_transformers"] = True
        except ImportError:
            pass
        
        try:
            import sklearn
            dependencies["sklearn"] = True
        except ImportError:
            pass
        
        try:
            import openai
            dependencies["openai"] = True
        except ImportError:
            pass
        
        try:
            import streamlit
            dependencies["streamlit"] = True
        except ImportError:
            pass
        
        all_available = all(dependencies.values())
        
        return {
            "status": "healthy" if all_available else "degraded",
            "message": "All dependencies available" if all_available else "Some dependencies missing",
            "details": dependencies
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics
        
        Returns:
            Dictionary with system metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {}
        }
        
        try:
            if self.db_manager:
                session = self.db_manager.get_session()
                try:
                    from utils.database import Review, AnalysisResult
                    from sqlalchemy import func
                    
                    review_count = session.query(func.count(Review.id)).scalar() or 0
                    analysis_count = session.query(func.count(AnalysisResult.id)).scalar() or 0
                    
                    metrics["database"] = {
                        "total_reviews": review_count,
                        "total_analyses": analysis_count
                    }
                finally:
                    session.close()
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            metrics["database"]["error"] = str(e)
        
        return metrics


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
