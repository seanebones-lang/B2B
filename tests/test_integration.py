"""Integration tests for the full pipeline"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, XAIClient
from utils.database import get_db_manager
from utils.cache import CacheManager
import config


class TestFullPipeline:
    """Test the complete scraping → analysis → storage pipeline"""
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample review data"""
        return [
            {
                "text": "This tool is missing critical features. I can't export my data properly.",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            },
            {
                "text": "The interface is confusing and lacks important functionality.",
                "rating": 1,
                "date": "2024-01-20",
                "source": "Capterra"
            },
            {
                "text": "I wish it had better integration options. The API is limited.",
                "rating": 2,
                "date": "2024-01-25",
                "source": "G2"
            }
        ]
    
    @pytest.fixture
    def mock_xai_client(self):
        """Mock xAI client"""
        client = Mock(spec=XAIClient)
        client.analyze_patterns.return_value = {
            "top_patterns": [
                {
                    "name": "Missing features",
                    "frequency": 2,
                    "impact_reason": "Blocks core workflows",
                    "example": "Can't export data"
                }
            ]
        }
        client.generate_product_ideas.return_value = [
            {
                "pattern": "Missing features",
                "ideas": [
                    {
                        "name": "Export Tool",
                        "type": "standalone",
                        "value_prop": "Easy data export",
                        "target": "Users needing data export",
                        "mvp_scope": "Export to CSV, JSON, Excel",
                        "monetization": "$29/mo"
                    }
                ]
            }
        ]
        client.generate_roadmap.return_value = {
            "week1": {"goal": "Validate", "tasks": ["Survey users"]},
            "week2": {"goal": "Build MVP", "tasks": ["Create landing page"]},
            "week3": {"goal": "Launch", "tasks": ["Post to Reddit"]},
            "week4": {"goal": "Iterate", "tasks": ["Collect feedback"]}
        }
        return client
    
    def test_pattern_extraction_pipeline(self, sample_reviews):
        """Test pattern extraction from reviews"""
        extractor = PatternExtractor()
        results = extractor.extract_patterns(sample_reviews)
        
        assert "patterns" in results
        assert "total_reviews" in results
        assert results["total_reviews"] == len(sample_reviews)
        assert isinstance(results["patterns"], list)
    
    def test_ai_analysis_pipeline(self, sample_reviews, mock_xai_client):
        """Test AI analysis of patterns"""
        extractor = PatternExtractor()
        pattern_results = extractor.extract_patterns(sample_reviews)
        
        ai_analysis = mock_xai_client.analyze_patterns(
            "Test Tool",
            pattern_results["patterns"],
            sample_reviews
        )
        
        assert "top_patterns" in ai_analysis
        assert len(ai_analysis["top_patterns"]) > 0
    
    def test_product_idea_generation(self, mock_xai_client):
        """Test product idea generation"""
        top_patterns = [
            {
                "name": "Missing features",
                "frequency": 2,
                "impact_reason": "Blocks workflows"
            }
        ]
        
        ideas = mock_xai_client.generate_product_ideas("Test Tool", top_patterns)
        
        assert isinstance(ideas, list)
        assert len(ideas) > 0
        assert "pattern" in ideas[0]
        assert "ideas" in ideas[0]
    
    def test_database_persistence(self, sample_reviews):
        """Test saving and retrieving reviews"""
        db_manager = get_db_manager()
        
        # Save reviews
        count = db_manager.save_reviews("Test Tool", sample_reviews)
        assert count == len(sample_reviews)
        
        # Retrieve reviews
        retrieved = db_manager.get_reviews("Test Tool", limit=10)
        assert len(retrieved) >= len(sample_reviews)
        
        # Verify data integrity
        assert retrieved[0]["text"] == sample_reviews[0]["text"]
        assert retrieved[0]["rating"] == sample_reviews[0]["rating"]
    
    def test_caching_integration(self, sample_reviews):
        """Test caching integration"""
        cache_manager = CacheManager()
        cache_key = "test_reviews"
        
        # Set cache
        cache_manager.set(cache_key, sample_reviews)
        
        # Get cache
        cached = cache_manager.get(cache_key)
        assert cached == sample_reviews
        
        # Clear cache
        cache_manager.clear()
        assert cache_manager.get(cache_key) is None
    
    @patch('scraper.g2_scraper.G2Scraper._fetch')
    def test_scraper_integration(self, mock_fetch):
        """Test scraper integration"""
        mock_response = Mock()
        mock_response.content = b"<html><body>No reviews</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_fetch.return_value = mock_response
        
        scraper = G2Scraper()
        reviews = scraper.scrape_reviews("Test Tool", max_reviews=10)
        
        assert isinstance(reviews, list)
        mock_fetch.assert_called()
    
    def test_full_pipeline_integration(self, sample_reviews, mock_xai_client):
        """Test complete pipeline: scrape → extract → analyze → generate"""
        # Step 1: Pattern extraction
        extractor = PatternExtractor()
        pattern_results = extractor.extract_patterns(sample_reviews)
        assert pattern_results["patterns"]
        
        # Step 2: AI analysis
        ai_analysis = mock_xai_client.analyze_patterns(
            "Test Tool",
            pattern_results["patterns"],
            sample_reviews
        )
        assert ai_analysis["top_patterns"]
        
        # Step 3: Product idea generation
        ideas = mock_xai_client.generate_product_ideas(
            "Test Tool",
            ai_analysis["top_patterns"]
        )
        assert ideas
        
        # Step 4: Roadmap generation
        if ideas and ideas[0].get("ideas"):
            roadmap = mock_xai_client.generate_roadmap(ideas[0]["ideas"][0])
            assert roadmap
            assert "week1" in roadmap


class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_scraper_error_handling(self):
        """Test scraper handles errors gracefully"""
        scraper = G2Scraper()
        
        # Should not raise exception on invalid input
        reviews = scraper.scrape_reviews("", max_reviews=0)
        assert isinstance(reviews, list)
    
    def test_ai_client_error_handling(self):
        """Test AI client handles errors"""
        # Invalid API key should raise ValueError
        with pytest.raises(ValueError):
            XAIClient("invalid_key")
    
    def test_database_error_handling(self):
        """Test database handles errors gracefully"""
        db_manager = get_db_manager()
        
        # Should handle empty data
        count = db_manager.save_reviews("Test", [])
        assert count == 0
        
        # Should return empty list for non-existent tool
        reviews = db_manager.get_reviews("NonExistentTool")
        assert isinstance(reviews, list)


class TestPerformance:
    """Test performance characteristics"""
    
    def test_pattern_extraction_performance(self):
        """Test pattern extraction performance"""
        import time
        
        # Generate large review set
        reviews = [
            {
                "text": f"Review {i}: This tool lacks feature {i % 10}",
                "rating": 1 if i % 2 == 0 else 2,
                "date": "2024-01-01",
                "source": "G2"
            }
            for i in range(100)
        ]
        
        extractor = PatternExtractor()
        
        start = time.time()
        results = extractor.extract_patterns(reviews)
        duration = time.time() - start
        
        # Should complete in reasonable time (< 5 seconds)
        assert duration < 5.0
        assert results["patterns"]
    
    def test_cache_performance(self):
        """Test cache performance"""
        import time
        
        cache_manager = CacheManager()
        data = list(range(1000))
        
        # First access (cache miss)
        start = time.time()
        cache_manager.set("perf_test", data)
        cache_manager.get("perf_test")
        first_duration = time.time() - start
        
        # Second access (cache hit)
        start = time.time()
        cached = cache_manager.get("perf_test")
        second_duration = time.time() - start
        
        # Cache hit should be faster
        assert second_duration < first_duration
        assert cached == data
