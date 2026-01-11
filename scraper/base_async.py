"""Async base scraper class with anti-detection mechanisms and improved error handling"""

import asyncio
import random
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

import httpx
from fake_useragent import UserAgent

from utils.logging import get_logger
from utils.retry import retry_scraper
from utils.compliance import ComplianceChecker
import config

logger = get_logger(__name__)


class BaseAsyncScraper(ABC):
    """Async base class for review scrapers with anti-detection features"""
    
    def __init__(
        self,
        delay_min: Optional[int] = None,
        delay_max: Optional[int] = None,
        timeout: Optional[int] = None,
        max_connections: int = 10
    ):
        """
        Initialize async base scraper
        
        Args:
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            timeout: Request timeout (seconds)
            max_connections: Maximum concurrent connections
        """
        self.ua = UserAgent()
        self.delay_min = delay_min or config.settings.scrape_delay_min
        self.delay_max = delay_max or config.settings.scrape_delay_max
        self.timeout = timeout or config.settings.scrape_timeout
        self.max_connections = max_connections
        self.compliance = ComplianceChecker()
        self.request_count = {}  # Track requests per domain
        
        # Create async HTTP client with connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=max_connections,
            max_connections=max_connections * 2
        )
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=limits,
            follow_redirects=True
        )
        
        logger.info(
            "Async base scraper initialized",
            delay_min=self.delay_min,
            delay_max=self.delay_max,
            timeout=self.timeout,
            max_connections=max_connections
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close client"""
        await self.client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Generate random headers to avoid detection
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    
    async def _delay(self) -> None:
        """Random delay between requests to avoid rate limiting"""
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.debug("Delaying request", delay_seconds=delay)
        await asyncio.sleep(delay)
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check robots.txt before fetching"""
        user_agent = self._get_headers().get("User-Agent", "*")
        return self.compliance.check_robots_txt(url, user_agent)
    
    async def _fetch(self, url: str, max_retries: int = 3) -> httpx.Response:
        """
        Fetch URL with retries and anti-detection (async)
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object
            
        Raises:
            Exception: If fetch fails after all retries
        """
        for attempt in range(max_retries):
            try:
                # Check robots.txt (only on first attempt)
                if attempt == 0:
                    if not self._check_robots_txt(url):
                        logger.warning("URL disallowed by robots.txt", url=url)
                        self.compliance.log_compliance_violation(url, "robots_txt")
                        raise RuntimeError(f"URL disallowed by robots.txt: {url}")
                
                # Throttle requests (1 req/sec per domain)
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain in self.request_count:
                    if self.compliance.should_throttle(domain, self.request_count[domain]):
                        await asyncio.sleep(1)
                else:
                    self.request_count[domain] = 0
                self.request_count[domain] = self.request_count.get(domain, 0) + 1
                
                await self._delay()
                logger.debug("Fetching URL", url=url, attempt=attempt + 1)
                
                response = await self.client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                logger.info(
                    "Successfully fetched URL",
                    url=url,
                    status_code=response.status_code
                )
                return response
                
            except httpx.TimeoutException as e:
                logger.error("Request timeout", url=url, attempt=attempt + 1, error=str(e))
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "HTTP error",
                    url=url,
                    status_code=e.response.status_code,
                    attempt=attempt + 1,
                    error=str(e)
                )
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                raise
                
            except httpx.RequestError as e:
                logger.error("Request failed", url=url, attempt=attempt + 1, error=str(e))
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        # This should never be reached as all exceptions are re-raised on last attempt
        # This is a safety fallback in case of unexpected control flow
        raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts - unexpected control flow")
    
    @abstractmethod
    async def scrape_reviews(
        self,
        tool_name: str,
        tool_slug: Optional[str] = None,
        tool_id: Optional[str] = None,
        max_reviews: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews for a given tool (async)
        
        Args:
            tool_name: Name of the tool
            tool_slug: G2 slug (optional)
            tool_id: Capterra ID (optional)
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            List of review dictionaries with keys: text, rating, date, source
        """
        pass
