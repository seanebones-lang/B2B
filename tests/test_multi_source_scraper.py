"""Tests for multi-source scraper"""

import pytest
from unittest.mock import Mock, patch
from scraper.multi_source_scraper import MultiSourceScraper


class TestMultiSourceScraper:
    """Test multi-source scraper functionality"""
    
    def test_init(self):
        """Test scraper initialization"""
        scraper = MultiSourceScraper()
        assert scraper.sources == []
    
    def test_scrape_all_sources_empty(self):
        """Test scraping with no sources available"""
        scraper = MultiSourceScraper()
        
        # Mock all scrapers to return empty lists
        with patch('scraper.multi_source_scraper.asyncio.run', return_value=[]):
            with patch('scraper.reddit_scraper.RedditScraper') as mock_reddit:
                mock_reddit.return_value.scrape_product_complaints.return_value = []
                
                reviews, sources = scraper.scrape_all_sources(
                    'TestTool',
                    max_per_source=10
                )
                
                assert isinstance(reviews, list)
                assert isinstance(sources, list)
    
    def test_date_filtering_propagation(self):
        """Test that date filters are passed to scrapers"""
        scraper = MultiSourceScraper()
        
        date_from = '2024-01-01'
        date_to = '2024-12-31'
        
        with patch('scraper.reddit_scraper.RedditScraper') as mock_reddit_class:
            mock_reddit = Mock()
            mock_reddit.scrape_product_complaints.return_value = []
            mock_reddit_class.return_value = mock_reddit
            
            scraper.scrape_all_sources(
                'TestTool',
                max_per_source=10,
                date_from=date_from,
                date_to=date_to
            )
            
            # Verify date filters were passed
            mock_reddit.scrape_product_complaints.assert_called()
            call_args = mock_reddit.scrape_product_complaints.call_args
            assert call_args.kwargs.get('date_from') == date_from
            assert call_args.kwargs.get('date_to') == date_to
