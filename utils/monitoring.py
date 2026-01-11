"""Monitoring utilities with Sentry and Prometheus support"""

from typing import Optional, Dict, Any
from utils.logging import get_logger
import os

logger = get_logger(__name__)

# Try to import Sentry
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

# Try to import Prometheus
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class MonitoringManager:
    """Monitoring manager for Sentry and Prometheus"""
    
    def __init__(self):
        """Initialize monitoring"""
        self.sentry_enabled = False
        self.prometheus_enabled = False
        
        # Initialize Sentry if available
        if SENTRY_AVAILABLE:
            self._init_sentry()
        
        # Initialize Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus()
    
    def _init_sentry(self):
        """Initialize Sentry error tracking"""
        try:
            sentry_dsn = os.getenv("SENTRY_DSN")
            
            # Try Streamlit secrets
            try:
                import streamlit as st
                sentry_dsn = st.secrets.get("sentry", {}).get("dsn") or sentry_dsn
            except:
                pass
            
            if sentry_dsn:
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[
                        LoggingIntegration(level=None, event_level=None)
                    ],
                    traces_sample_rate=0.1,  # 10% of transactions
                    environment=os.getenv("ENVIRONMENT", "development")
                )
                self.sentry_enabled = True
                logger.info("Sentry monitoring initialized")
            else:
                logger.info("Sentry DSN not found, skipping Sentry initialization")
        except Exception as e:
            logger.warning("Failed to initialize Sentry", error=str(e))
    
    def _init_prometheus(self):
        """Initialize Prometheus metrics"""
        try:
            # Define metrics
            self.scrape_requests_total = Counter(
                'scrape_requests_total',
                'Total number of scrape requests',
                ['source', 'status']
            )
            
            self.scrape_duration_seconds = Histogram(
                'scrape_duration_seconds',
                'Time spent scraping',
                ['source']
            )
            
            self.reviews_scraped_total = Counter(
                'reviews_scraped_total',
                'Total number of reviews scraped',
                ['source', 'tool']
            )
            
            self.ai_requests_total = Counter(
                'ai_requests_total',
                'Total number of AI API requests',
                ['model', 'status']
            )
            
            self.active_scrapes = Gauge(
                'active_scrapes',
                'Number of active scraping operations'
            )
            
            # Start Prometheus HTTP server if enabled
            prometheus_port = int(os.getenv("PROMETHEUS_PORT", "0"))
            if prometheus_port > 0:
                start_http_server(prometheus_port)
                logger.info("Prometheus metrics server started", port=prometheus_port)
            
            self.prometheus_enabled = True
            logger.info("Prometheus metrics initialized")
            
        except Exception as e:
            logger.warning("Failed to initialize Prometheus", error=str(e))
    
    def track_scrape_request(self, source: str, status: str = "success"):
        """Track a scrape request"""
        if self.prometheus_enabled:
            self.scrape_requests_total.labels(source=source, status=status).inc()
    
    def track_scrape_duration(self, source: str, duration: float):
        """Track scrape duration"""
        if self.prometheus_enabled:
            self.scrape_duration_seconds.labels(source=source).observe(duration)
    
    def track_reviews_scraped(self, source: str, tool: str, count: int):
        """Track reviews scraped"""
        if self.prometheus_enabled:
            self.reviews_scraped_total.labels(source=source, tool=tool).inc(count)
    
    def track_ai_request(self, model: str, status: str = "success"):
        """Track AI API request"""
        if self.prometheus_enabled:
            self.ai_requests_total.labels(model=model, status=status).inc()
    
    def set_active_scrapes(self, count: int):
        """Set number of active scrapes"""
        if self.prometheus_enabled:
            self.active_scrapes.set(count)
    
    def capture_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Capture exception in Sentry"""
        if self.sentry_enabled:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                sentry_sdk.capture_exception(error)


# Global monitoring instance
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring() -> MonitoringManager:
    """Get global monitoring manager instance"""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager()
    return _monitoring_manager
