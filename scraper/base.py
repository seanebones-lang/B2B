"""Base scraper class with anti-detection mechanisms"""

import time
import random
import requests
from fake_useragent import UserAgent
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Base class for review scrapers with anti-detection features"""
    
    def __init__(self, delay_min=2, delay_max=5, timeout=30):
        self.ua = UserAgent()
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.timeout = timeout
        self.session = requests.Session()
    
    def _get_headers(self):
        """Generate random headers to avoid detection"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def _delay(self):
        """Random delay between requests"""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def _fetch(self, url, max_retries=3):
        """Fetch URL with retries and anti-detection"""
        for attempt in range(max_retries):
            try:
                self._delay()
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to fetch {url} after {max_retries} attempts: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    @abstractmethod
    def scrape_reviews(self, tool_name, tool_slug=None, tool_id=None, max_reviews=30):
        """
        Scrape reviews for a given tool
        Returns list of dicts: [{text, rating, date, source}, ...]
        """
        pass
