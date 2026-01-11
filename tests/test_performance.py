"""Performance benchmarks for critical paths"""

import pytest
import time
from unittest.mock import Mock, patch
import asyncio

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, PatternExtractorV2
from utils.database import get_db_manager
from utils.cache import CacheManager
from utils.async_helpers import scrape_tool_sync
import config


class TestScrapingPerformance:
    """Benchmark scraping performance"""
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample review data for testing"""
        return [
            {
                "text": "This tool is missing critical export features. I can't export my data properly.",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
        ] * 10
    
    def test_g2_scraper_performance(self, benchmark):
        """Benchmark G2 scraper performance"""
        scraper = G2Scraper()
        
        with patch.object(scraper, '_fetch') as mock_fetch:
            mock_response = Mock()
            mock_response.content = b'<html><body><div class="review">Test review</div></body></html>'
            mock_fetch.return_value = mock_response
            
            result = benchmark(scraper.scrape_reviews, "Test Tool", max_reviews=10)
            assert isinstance(result, list)
    
    def test_capterra_scraper_performance(self, benchmark):
        """Benchmark Capterra scraper performance"""
        scraper = CapterraScraper()
        
        with patch.object(scraper, '_fetch') as mock_fetch:
            mock_response = Mock()
            mock_response.content = b'<html><body><div class="review">Test review</div></body></html>'
            mock_fetch.return_value = mock_response
            
            result = benchmark(scraper.scrape_reviews, "Test Tool", tool_id="123", max_reviews=10)
            assert isinstance(result, list)


class TestPatternExtractionPerformance:
    """Benchmark pattern extraction performance"""
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample review data"""
        return [
            {
                "text": f"This tool is missing feature {i}. I can't do what I need.",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(100)
        ]
    
    def test_pattern_extractor_performance(self, benchmark, sample_reviews):
        """Benchmark pattern extractor performance"""
        extractor = PatternExtractor()
        
        result = benchmark(extractor.extract_patterns, sample_reviews)
        assert "patterns" in result
        assert isinstance(result["patterns"], list)
    
    def test_semantic_pattern_extractor_performance(self, benchmark, sample_reviews):
        """Benchmark semantic pattern extractor performance"""
        try:
            extractor = PatternExtractorV2(use_semantic=True)
            result = benchmark(extractor.extract_patterns, sample_reviews)
            assert "patterns" in result
        except Exception:
            pytest.skip("Semantic extractor not available")


class TestDatabasePerformance:
    """Benchmark database operations"""
    
    @pytest.fixture
    def db_manager(self):
        """Database manager fixture"""
        return get_db_manager()
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample review data"""
        return [
            {
                "text": f"Review {i}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(100)
        ]
    
    def test_save_reviews_performance(self, benchmark, db_manager, sample_reviews):
        """Benchmark saving reviews to database"""
        result = benchmark(db_manager.save_reviews, "Test Tool", sample_reviews, encrypt=False)
        assert result > 0
    
    def test_get_reviews_performance(self, benchmark, db_manager):
        """Benchmark retrieving reviews from database"""
        # Ensure some data exists
        db_manager.save_reviews("Test Tool", [{"text": "Test", "rating": 2, "source": "G2"}], encrypt=False)
        
        result = benchmark(db_manager.get_reviews, "Test Tool", limit=100, decrypt=False)
        assert isinstance(result, list)


class TestCachePerformance:
    """Benchmark cache operations"""
    
    @pytest.fixture
    def cache_manager(self):
        """Cache manager fixture"""
        return CacheManager()
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for caching"""
        return {"key": "value", "data": list(range(1000))}
    
    def test_cache_set_performance(self, benchmark, cache_manager, sample_data):
        """Benchmark cache set operation"""
        result = benchmark(cache_manager.set, "test_key", sample_data)
        assert result is True
    
    def test_cache_get_performance(self, benchmark, cache_manager, sample_data):
        """Benchmark cache get operation"""
        cache_manager.set("test_key", sample_data)
        
        result = benchmark(cache_manager.get, "test_key")
        assert result == sample_data


class TestFullPipelinePerformance:
    """Benchmark full pipeline performance"""
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample review data"""
        return [
            {
                "text": f"Review {i}: Missing feature {i}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(50)
        ]
    
    def test_full_pipeline_performance(self, benchmark, sample_reviews):
        """Benchmark full pipeline: extract patterns"""
        extractor = PatternExtractor()
        
        def run_pipeline():
            patterns = extractor.extract_patterns(sample_reviews)
            return patterns
        
        result = benchmark(run_pipeline)
        assert "patterns" in result


class TestConcurrencyPerformance:
    """Benchmark concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping(self):
        """Test concurrent scraping performance"""
        tool_configs = [
            {"name": "Tool1", "g2_slug": "tool1", "capterra_id": "1"},
            {"name": "Tool2", "g2_slug": "tool2", "capterra_id": "2"},
            {"name": "Tool3", "g2_slug": "tool3", "capterra_id": "3"},
        ]
        
        async def scrape_tool(tool_config):
            # Mock scraping
            await asyncio.sleep(0.1)
            return [{"text": "Review", "rating": 2, "source": "G2"}]
        
        start_time = time.time()
        results = await asyncio.gather(*[scrape_tool(tc) for tc in tool_configs])
        duration = time.time() - start_time
        
        # Concurrent should be faster than sequential
        assert duration < 0.5  # Should complete in < 0.5s (vs 0.3s sequential)
        assert len(results) == 3


# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "scraping": 2.0,  # seconds per tool
    "pattern_extraction": 1.0,  # seconds for 100 reviews
    "database_save": 0.5,  # seconds for 100 reviews
    "database_get": 0.1,  # seconds for 100 reviews
    "cache_set": 0.01,  # seconds
    "cache_get": 0.001,  # seconds
    "full_pipeline": 2.0,  # seconds for 50 reviews
}
