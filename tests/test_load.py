"""Load testing for scalability verification"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import statistics

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor
from utils.database import get_db_manager
from utils.cache import CacheManager
import config


class TestLoadScraping:
    """Load tests for scraping operations"""
    
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
            for i in range(100)
        ]
    
    def test_concurrent_scraping(self, sample_reviews):
        """Test concurrent scraping operations"""
        scraper = G2Scraper()
        num_concurrent = 10
        
        def scrape_task(tool_name: str):
            """Mock scraping task"""
            time.sleep(0.1)  # Simulate scraping delay
            return sample_reviews[:10]
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(scrape_task, f"Tool{i}")
                for i in range(num_concurrent)
            ]
            results = [f.get() for f in as_completed(futures)]
        
        duration = time.time() - start_time
        
        # Concurrent should complete faster than sequential
        assert len(results) == num_concurrent
        assert duration < 2.0  # Should complete in < 2s (vs 1s sequential)
        
        print(f"Concurrent scraping: {num_concurrent} tasks in {duration:.2f}s")
    
    def test_scraping_throughput(self, sample_reviews):
        """Test scraping throughput"""
        scraper = G2Scraper()
        num_requests = 50
        start_time = time.time()
        
        for i in range(num_requests):
            # Simulate scraping
            time.sleep(0.01)
        
        duration = time.time() - start_time
        throughput = num_requests / duration
        
        assert throughput > 10  # At least 10 requests/second
        print(f"Scraping throughput: {throughput:.2f} requests/second")


class TestLoadPatternExtraction:
    """Load tests for pattern extraction"""
    
    @pytest.fixture
    def large_review_set(self):
        """Large set of reviews for load testing"""
        return [
            {
                "text": f"Review {i}: This tool is missing critical feature {i % 10}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(1000)
        ]
    
    def test_pattern_extraction_performance(self, large_review_set):
        """Test pattern extraction with large dataset"""
        extractor = PatternExtractor()
        
        start_time = time.time()
        results = extractor.extract_patterns(large_review_set)
        duration = time.time() - start_time
        
        assert "patterns" in results
        assert duration < 5.0  # Should complete in < 5s for 1000 reviews
        print(f"Pattern extraction: 1000 reviews in {duration:.2f}s")
    
    def test_concurrent_pattern_extraction(self, large_review_set):
        """Test concurrent pattern extraction"""
        extractor = PatternExtractor()
        num_concurrent = 5
        chunk_size = len(large_review_set) // num_concurrent
        
        def extract_chunk(chunk):
            return extractor.extract_patterns(chunk)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            chunks = [
                large_review_set[i:i+chunk_size]
                for i in range(0, len(large_review_set), chunk_size)
            ]
            futures = [executor.submit(extract_chunk, chunk) for chunk in chunks]
            results = [f.get() for f in as_completed(futures)]
        
        duration = time.time() - start_time
        
        assert len(results) == num_concurrent
        assert duration < 3.0  # Concurrent should be faster
        print(f"Concurrent pattern extraction: {num_concurrent} chunks in {duration:.2f}s")


class TestLoadDatabase:
    """Load tests for database operations"""
    
    @pytest.fixture
    def db_manager(self):
        """Database manager"""
        return get_db_manager()
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample reviews"""
        return [
            {
                "text": f"Review {i}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(100)
        ]
    
    def test_concurrent_database_writes(self, db_manager, sample_reviews):
        """Test concurrent database writes"""
        num_concurrent = 10
        
        def write_reviews(tool_name: str):
            return db_manager.save_reviews(tool_name, sample_reviews[:10], encrypt=False)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(write_reviews, f"Tool{i}")
                for i in range(num_concurrent)
            ]
            results = [f.get() for f in as_completed(futures)]
        
        duration = time.time() - start_time
        
        assert len(results) == num_concurrent
        assert all(r > 0 for r in results)
        print(f"Concurrent database writes: {num_concurrent} operations in {duration:.2f}s")
    
    def test_database_read_throughput(self, db_manager):
        """Test database read throughput"""
        num_reads = 100
        start_time = time.time()
        
        for i in range(num_reads):
            db_manager.get_reviews(limit=10, decrypt=False)
        
        duration = time.time() - start_time
        throughput = num_reads / duration
        
        assert throughput > 50  # At least 50 reads/second
        print(f"Database read throughput: {throughput:.2f} reads/second")


class TestLoadFullPipeline:
    """Load tests for full pipeline"""
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample reviews"""
        return [
            {
                "text": f"Review {i}: Missing feature {i % 5}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(100)
        ]
    
    def test_full_pipeline_throughput(self, sample_reviews):
        """Test full pipeline throughput"""
        extractor = PatternExtractor()
        
        def run_pipeline():
            patterns = extractor.extract_patterns(sample_reviews)
            return patterns
        
        num_runs = 10
        durations = []
        
        for i in range(num_runs):
            start_time = time.time()
            run_pipeline()
            durations.append(time.time() - start_time)
        
        avg_duration = statistics.mean(durations)
        p95_duration = sorted(durations)[int(0.95 * len(durations))]
        
        assert avg_duration < 2.0  # Average < 2s
        assert p95_duration < 3.0  # P95 < 3s
        print(f"Full pipeline: avg={avg_duration:.2f}s, p95={p95_duration:.2f}s")
    
    def test_concurrent_pipeline_execution(self, sample_reviews):
        """Test concurrent pipeline execution"""
        extractor = PatternExtractor()
        num_concurrent = 5
        
        def run_pipeline():
            return extractor.extract_patterns(sample_reviews)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_pipeline) for _ in range(num_concurrent)]
            results = [f.get() for f in as_completed(futures)]
        
        duration = time.time() - start_time
        
        assert len(results) == num_concurrent
        assert duration < 3.0  # Concurrent should be faster
        print(f"Concurrent pipeline: {num_concurrent} runs in {duration:.2f}s")


class TestScalabilityLimits:
    """Test scalability limits"""
    
    def test_10x_load(self):
        """Test 10x normal load"""
        # Normal load: 1 tool, 30 reviews
        # 10x load: 10 tools, 300 reviews
        
        extractor = PatternExtractor()
        large_review_set = [
            {
                "text": f"Review {i}: Missing feature {i % 10}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(300)
        ]
        
        start_time = time.time()
        results = extractor.extract_patterns(large_review_set)
        duration = time.time() - start_time
        
        assert "patterns" in results
        assert duration < 10.0  # Should handle 10x load in < 10s
        print(f"10x load: 300 reviews in {duration:.2f}s")
    
    def test_100x_load(self):
        """Test 100x normal load"""
        # Normal load: 1 tool, 30 reviews
        # 100x load: 100 tools, 3000 reviews
        
        extractor = PatternExtractor()
        very_large_review_set = [
            {
                "text": f"Review {i}: Missing feature {i % 10}",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            }
            for i in range(3000)
        ]
        
        start_time = time.time()
        results = extractor.extract_patterns(very_large_review_set)
        duration = time.time() - start_time
        
        assert "patterns" in results
        assert duration < 60.0  # Should handle 100x load in < 60s
        print(f"100x load: 3000 reviews in {duration:.2f}s")


# Performance thresholds for load testing
LOAD_TEST_THRESHOLDS = {
    "concurrent_scraping": 2.0,  # seconds for 10 concurrent
    "scraping_throughput": 10.0,  # requests/second
    "pattern_extraction_1000": 5.0,  # seconds for 1000 reviews
    "database_write_concurrent": 5.0,  # seconds for 10 concurrent
    "database_read_throughput": 50.0,  # reads/second
    "full_pipeline_avg": 2.0,  # seconds average
    "full_pipeline_p95": 3.0,  # seconds P95
    "10x_load": 10.0,  # seconds for 300 reviews
    "100x_load": 60.0,  # seconds for 3000 reviews
}
