"""Base scraper class with anti-detection mechanisms and improved error handling"""

import time
import random
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

import requests
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logging import get_logger
from utils.retry import retry_scraper
from utils.circuit_breaker import get_circuit_breaker
from utils.compliance import ComplianceChecker
import config

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Base class for review scrapers with anti-detection features"""
    
    def __init__(
        self,
        delay_min: Optional[int] = None,
        delay_max: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> None:
        """
        Initialize base scraper
        
        Args:
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            timeout: Request timeout (seconds)
        """
        self.ua = UserAgent()
        self.delay_min = delay_min or config.settings.scrape_delay_min
        self.delay_max = delay_max or config.settings.scrape_delay_max
        self.timeout = timeout or config.settings.scrape_timeout
        self.compliance = ComplianceChecker()
        self.request_count = {}  # Track requests per domain
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(
            "Base scraper initialized",
            delay_min=self.delay_min,
            delay_max=self.delay_max,
            timeout=self.timeout
        )
    
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
    
    def _delay(self) -> None:
        """Random delay between requests to avoid rate limiting"""
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.debug("Delaying request", delay_seconds=delay)
        time.sleep(delay)
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check robots.txt before fetching"""
        user_agent = self._get_headers().get("User-Agent", "*")
        return self.compliance.check_robots_txt(url, user_agent)
    
    @retry_scraper(max_attempts=3)
    def _fetch(self, url: str, max_retries: int = 3) -> requests.Response:
        """
        Fetch URL with retries, anti-detection, and circuit breaker protection
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object
            
        Raises:
            Exception: If fetch fails after all retries or circuit breaker is open
        """
        # Validate URL
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL provided")
        
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"URL must start with http:// or https://: {url}")
        
        # Get circuit breaker for scraper
        breaker = get_circuit_breaker(
            "scraper",
            failure_threshold=5,
            timeout=60,
            expected_exception=(
                requests.exceptions.RequestException,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError
            )
        )
        
        def _make_request():
            """Make HTTP request wrapped in circuit breaker"""
            # Check robots.txt before making request
            if not self._check_robots_txt(url):
                logger.warning("URL disallowed by robots.txt", url=url)
                self.compliance.log_compliance_violation(url, "robots_txt")
                raise RuntimeError(f"URL disallowed by robots.txt: {url}")
            
            # Throttle requests (1 req/sec per domain)
            from urllib.parse import urlparse
            import time
            domain = urlparse(url).netloc
            if domain in self.request_count:
                if self.compliance.should_throttle(domain, self.request_count[domain]):
                    time.sleep(1)
                    # Reset counter after throttling
                    self.request_count[domain] = 0
            else:
                self.request_count[domain] = 0
            self.request_count[domain] = self.request_count.get(domain, 0) + 1
            
            self._delay()
            logger.debug("Fetching URL", url=url)
            
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Validate response content
            if not response.content:
                logger.warning("Empty response received", url=url)
                raise ValueError("Empty response received")
            
            logger.info(
                "Successfully fetched URL",
                url=url,
                status_code=response.status_code,
                content_length=len(response.content)
            )
            return response
        
        try:
            # Use circuit breaker to protect request
            return breaker.call(_make_request)
            
        except requests.exceptions.Timeout as e:
            logger.error("Request timeout", url=url, error=str(e))
            raise requests.exceptions.Timeout(f"Request timeout: {url}") from e
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            logger.error(
                "HTTP error",
                url=url,
                status_code=status_code,
                error=str(e)
            )
            
            # Handle specific status codes
            if status_code == 429:  # Rate limited
                if e.response and e.response.headers:
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                else:
                    retry_after = 60
                logger.warning("Rate limited", url=url, retry_after=retry_after)
                raise requests.exceptions.HTTPError(
                    f"Rate limited. Retry after {retry_after} seconds: {url}"
                ) from e
            
            if status_code == 404:  # Not found - don't retry
                raise requests.exceptions.HTTPError(f"Resource not found: {url}") from e
            
            raise
            
        except requests.exceptions.RequestException as e:
            logger.error("Request failed", url=url, error=str(e))
            raise requests.exceptions.RequestException(f"Request failed: {url}") from e
            
        except Exception as e:
            logger.error(
                "Unexpected error in _fetch",
                url=url,
                error=str(e),
                error_type=type(e).__name__
            )
            # Preserve original exception type instead of raising generic Exception
            # This maintains exception type information for better error handling upstream
            raise type(e)(f"Unexpected error fetching {url}: {str(e)}") from e
    
    @abstractmethod
    def scrape_reviews(
        self,
        tool_name: str,
        tool_slug: Optional[str] = None,
        tool_id: Optional[str] = None,
        max_reviews: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews for a given tool
        
        Args:
            tool_name: Name of the tool
            tool_slug: G2 slug (optional)
            tool_id: Capterra ID (optional)
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            List of review dictionaries with keys: text, rating, date, source
        """
        pass
