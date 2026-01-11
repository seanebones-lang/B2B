"""Tests for scraper modules"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from scraper.base import BaseScraper
from scraper.g2_scraper import G2Scraper
from scraper.capterra_scraper import CapterraScraper


class TestBaseScraper:
    """Test base scraper functionality"""
    
    def test_init(self):
        """Test scraper initialization"""
        scraper = BaseScraper(delay_min=1, delay_max=2, timeout=10)
        assert scraper.delay_min == 1
        assert scraper.delay_max == 2
        assert scraper.timeout == 10
        assert scraper.session is not None
    
    def test_get_headers(self):
        """Test header generation"""
        scraper = BaseScraper()
        headers = scraper._get_headers()
        
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
    
    @patch('time.sleep')
    def test_delay(self, mock_sleep):
        """Test delay functionality"""
        scraper = BaseScraper(delay_min=1, delay_max=2)
        scraper._delay()
        mock_sleep.assert_called_once()
        # Check delay is within range
        call_args = mock_sleep.call_args[0][0]
        assert 1 <= call_args <= 2
    
    @patch('scraper.base.BaseScraper._delay')
    @patch('requests.Session.get')
    def test_fetch_success(self, mock_get, mock_delay):
        """Test successful fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html>test</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = BaseScraper()
        response = scraper._fetch("http://example.com")
        
        assert response == mock_response
        mock_get.assert_called_once()
        mock_delay.assert_called_once()
    
    @patch('scraper.base.BaseScraper._delay')
    @patch('requests.Session.get')
    def test_fetch_retry_on_failure(self, mock_get, mock_delay):
        """Test retry on fetch failure"""
        mock_get.side_effect = [
            Exception("Network error"),
            Mock(status_code=200, content=b"<html>test</html>", raise_for_status=Mock())
        ]
        
        scraper = BaseScraper()
        response = scraper._fetch("http://example.com")
        
        assert mock_get.call_count == 2
        assert mock_delay.call_count == 2


class TestG2Scraper:
    """Test G2 scraper"""
    
    def test_init(self):
        """Test G2 scraper initialization"""
        scraper = G2Scraper()
        assert isinstance(scraper, BaseScraper)
    
    @patch('scraper.g2_scraper.G2Scraper._fetch')
    def test_scrape_reviews_no_slug(self, mock_fetch):
        """Test scraping with tool name only"""
        mock_response = Mock()
        mock_response.content = b"<html><body>No reviews</body></html>"
        mock_fetch.return_value = mock_response
        
        scraper = G2Scraper()
        reviews = scraper.scrape_reviews("Test Tool", max_reviews=10)
        
        assert isinstance(reviews, list)
        # Should attempt to fetch
        assert mock_fetch.called
    
    @patch('scraper.g2_scraper.G2Scraper._fetch')
    def test_scrape_reviews_with_reviews(self, mock_fetch):
        """Test scraping with actual review HTML"""
        html_content = """
        <html>
            <body>
                <div class="review">
                    <p class="review-text">This tool is terrible. It lacks basic features.</p>
                    <span class="rating">1</span>
                    <time class="date">2024-01-01</time>
                </div>
                <div class="review">
                    <p class="review-text">Very disappointed with the user interface.</p>
                    <span class="rating">2</span>
                    <time class="date">2024-01-02</time>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html_content.encode()
        mock_fetch.return_value = mock_response
        
        scraper = G2Scraper()
        reviews = scraper.scrape_reviews("Test Tool", tool_slug="test-tool", max_reviews=10)
        
        assert len(reviews) == 2
        assert reviews[0]["rating"] <= 2
        assert reviews[0]["source"] == "G2"
        assert "text" in reviews[0]
    
    @patch('scraper.g2_scraper.G2Scraper._fetch')
    def test_scrape_reviews_filters_high_ratings(self, mock_fetch):
        """Test that high ratings are filtered out"""
        html_content = """
        <html>
            <body>
                <div class="review">
                    <p class="review-text">Great tool!</p>
                    <span class="rating">5</span>
                </div>
                <div class="review">
                    <p class="review-text">Bad tool.</p>
                    <span class="rating">1</span>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html_content.encode()
        mock_fetch.return_value = mock_response
        
        scraper = G2Scraper()
        reviews = scraper.scrape_reviews("Test Tool", tool_slug="test-tool", max_reviews=10)
        
        # Should only include 1-2 star reviews
        assert len(reviews) == 1
        assert reviews[0]["rating"] == 1


class TestCapterraScraper:
    """Test Capterra scraper"""
    
    def test_init(self):
        """Test Capterra scraper initialization"""
        scraper = CapterraScraper()
        assert isinstance(scraper, BaseScraper)
    
    @patch('scraper.capterra_scraper.CapterraScraper._fetch')
    def test_scrape_reviews_with_tool_id(self, mock_fetch):
        """Test scraping with tool ID"""
        html_content = """
        <html>
            <body>
                <div class="review">
                    <p class="review-text">Missing critical features.</p>
                    <span class="rating">1</span>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html_content.encode()
        mock_fetch.return_value = mock_response
        
        scraper = CapterraScraper()
        reviews = scraper.scrape_reviews("Test Tool", tool_id="123", max_reviews=10)
        
        assert isinstance(reviews, list)
        if reviews:
            assert reviews[0]["source"] == "Capterra"
    
    @patch('scraper.capterra_scraper.CapterraScraper._fetch')
    def test_scrape_reviews_no_tool_id(self, mock_fetch):
        """Test scraping without tool ID"""
        # Mock search page with no product link
        mock_response = Mock()
        mock_response.content = b"<html><body>No product found</body></html>"
        mock_fetch.return_value = mock_response
        
        scraper = CapterraScraper()
        reviews = scraper.scrape_reviews("Unknown Tool", max_reviews=10)
        
        assert reviews == []
