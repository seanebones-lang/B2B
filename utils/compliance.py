"""Compliance module for ethical scraping practices"""

import urllib.robotparser
from typing import Optional, Dict, List
from urllib.parse import urlparse
from utils.logging import get_logger

logger = get_logger(__name__)


class ComplianceChecker:
    """Check robots.txt and enforce ethical scraping practices"""
    
    def __init__(self):
        """Initialize compliance checker"""
        self.robots_cache: Dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
        logger.info("Compliance checker initialized")
    
    def check_robots_txt(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if URL is allowed by robots.txt
        
        Args:
            url: URL to check
            user_agent: User agent string (default: "*" for all)
            
        Returns:
            True if allowed, False if disallowed
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Check cache
            cache_key = f"{base_url}:{user_agent}"
            if cache_key in self.robots_cache:
                rp = self.robots_cache[cache_key]
                if rp is None:
                    return True  # No robots.txt found, allow by default
                return rp.can_fetch(user_agent, url)
            
            # Fetch robots.txt
            robots_url = f"{base_url}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            
            try:
                rp.read()
                self.robots_cache[cache_key] = rp
                allowed = rp.can_fetch(user_agent, url)
                logger.info("Robots.txt checked", url=url, allowed=allowed, user_agent=user_agent)
                return allowed
            except Exception as e:
                logger.warning("Could not fetch robots.txt", url=robots_url, error=str(e))
                # If robots.txt doesn't exist or can't be fetched, allow by default
                self.robots_cache[cache_key] = None
                return True
                
        except Exception as e:
            logger.error("Error checking robots.txt", url=url, error=str(e))
            # On error, allow by default but log it
            return True
    
    def log_compliance_violation(self, url: str, violation_type: str, details: str = ""):
        """
        Log a potential compliance violation
        
        Args:
            url: URL where violation occurred
            violation_type: Type of violation (e.g., "robots_txt", "rate_limit")
            details: Additional details
        """
        logger.warning(
            "Compliance violation detected",
            url=url,
            violation_type=violation_type,
            details=details
        )
    
    def should_throttle(self, domain: str, request_count: int, time_window: int = 1) -> bool:
        """
        Check if requests should be throttled based on domain
        
        Args:
            domain: Domain name
            request_count: Number of requests made (tracked by caller)
            time_window: Time window in seconds (default: 1 for 1 req/sec)
            
        Returns:
            True if should throttle (rate limit exceeded)
        """
        # Rate limiting: 1 request per second per domain
        # If we've made a request in this time window, throttle
        # Note: This is a simple implementation - caller should reset count after delay
        # For production, use a proper rate limiter with timestamps (e.g., Redis)
        if request_count >= 1:
            logger.debug("Throttling request", domain=domain, count=request_count)
            return True
        return False
