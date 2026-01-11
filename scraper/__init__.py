"""Review scrapers for G2.com and Capterra"""

from .g2_scraper import G2Scraper
from .capterra_scraper import CapterraScraper
from .base import BaseScraper

__all__ = ["G2Scraper", "CapterraScraper", "BaseScraper"]
