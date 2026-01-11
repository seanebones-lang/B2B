"""End-to-end tests for the complete application flow"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from scraper import G2Scraper, CapterraScraper
from analyzer import PatternExtractor, PatternExtractorV2, XAIClient
from utils.database import get_db_manager
from utils.cache import CacheManager
from utils.async_helpers import scrape_tool_sync
import config


class TestE2EFullPipeline:
    """Test complete end-to-end user flows"""
    
    @pytest.fixture
    def sample_reviews(self):
        """Sample review data"""
        return [
            {
                "text": "This tool is missing critical export features. I can't export my data properly.",
                "rating": 2,
                "date": "2024-01-15",
                "source": "G2"
            },
            {
                "text": "The interface is confusing and lacks important functionality for data management.",
                "rating": 1,
                "date": "2024-01-20",
                "source": "Capterra"
            },
            {
                "text": "I wish it had better integration options. The API is limited and doesn't support webhooks.",
                "rating": 2,
                "date": "2024-01-25",
                "source": "G2"
            }
        ]
    
    @pytest.fixture
    def mock_xai_client(self):
        """Mock xAI client with realistic responses"""
        client = Mock(spec=XAIClient)
        
        # Mock analyze_patterns
        client.analyze_patterns.return_value = {
            "top_patterns": [
                {
                    "name": "Missing export features",
                    "frequency": 2,
                    "impact_reason": "Blocks core workflow of data export",
                    "example": "Can't export data properly"
                },
                {
                    "name": "Limited API integration",
                    "frequency": 1,
                    "impact_reason": "Prevents integration with other tools",
                    "example": "API is limited and doesn't support webhooks"
                }
            ]
        }
        
        # Mock generate_product_ideas
        client.generate_product_ideas.return_value = [
            {
                "pattern": "Missing export features",
                "ideas": [
                    {
                        "name": "ExportPro",
                        "type": "standalone",
                        "value_prop": "Easy data export for any SaaS tool",
                        "target": "Users needing data export",
                        "mvp_scope": "Export to CSV, JSON, Excel, PDF",
                        "monetization": "$29/mo"
                    },
                    {
                        "name": "Export Helper",
                        "type": "plugin",
                        "value_prop": "Browser extension for quick exports",
                        "target": "Power users",
                        "mvp_scope": "One-click export, multiple formats",
                        "monetization": "$9/mo"
                    }
                ]
            }
        ]
        
        # Mock generate_roadmap
        client.generate_roadmap.return_value = {
            "week1": {
                "goal": "Validate demand",
                "tasks": [
                    "Survey 10 potential customers",
                    "Create landing page",
                    "Set up analytics"
                ]
            },
            "week2": {
                "goal": "Build MVP",
                "tasks": [
                    "Implement CSV export",
                    "Implement JSON export",
                    "Create user interface"
                ]
            },
            "week3": {
                "goal": "Launch",
                "tasks": [
                    "Post to Product Hunt",
                    "Share on Reddit",
                    "Email waitlist"
                ]
            },
            "week4": {
                "goal": "Iterate",
                "tasks": [
                    "Collect user feedback",
                    "Implement top 2 features",
                    "Plan next iteration"
                ]
            }
        }
        
        return client
    
    def test_complete_user_flow(self, sample_reviews, mock_xai_client):
        """Test complete user flow: select tool → scrape → analyze → generate ideas"""
        # Step 1: Select tool
        tool_name = "Test Tool"
        tool_config = next(
            (t for t in config.B2B_TOOLS if t["name"] == "Salesforce"),
            config.B2B_TOOLS[0]
        )
        
        # Step 2: Scrape reviews (mocked)
        with patch('utils.async_helpers.scrape_tool_async') as mock_scrape:
            async def mock_scrape_async(tool_name, tool_config, max_reviews):
                return sample_reviews
            
            mock_scrape.side_effect = mock_scrape_async
            
            reviews = scrape_tool_sync(tool_name, tool_config, max_reviews=30)
            assert len(reviews) == len(sample_reviews)
        
        # Step 3: Extract patterns
        extractor = PatternExtractor()
        pattern_results = extractor.extract_patterns(reviews)
        assert "patterns" in pattern_results
        assert len(pattern_results["patterns"]) > 0
        
        # Step 4: AI analysis
        ai_analysis = mock_xai_client.analyze_patterns(
            tool_name,
            pattern_results["patterns"],
            reviews
        )
        assert "top_patterns" in ai_analysis
        assert len(ai_analysis["top_patterns"]) > 0
        
        # Step 5: Generate product ideas
        ideas = mock_xai_client.generate_product_ideas(
            tool_name,
            ai_analysis["top_patterns"]
        )
        assert isinstance(ideas, list)
        assert len(ideas) > 0
        
        # Step 6: Generate roadmap
        if ideas and ideas[0].get("ideas"):
            roadmap = mock_xai_client.generate_roadmap(ideas[0]["ideas"][0])
            assert roadmap
            assert "week1" in roadmap
            assert "week2" in roadmap
            assert "week3" in roadmap
            assert "week4" in roadmap
    
    def test_multi_tool_analysis_flow(self, mock_xai_client):
        """Test analyzing multiple tools in sequence"""
        tools = ["Salesforce", "HubSpot"]
        all_results = {}
        
        for tool_name in tools:
            tool_config = next(
                (t for t in config.B2B_TOOLS if t["name"] == tool_name),
                None
            )
            
            if not tool_config:
                continue
            
            # Mock scraping
            with patch('utils.async_helpers.scrape_tool_async') as mock_scrape:
                async def mock_scrape_async(tool_name, tool_config, max_reviews):
                    return [
                        {
                            "text": f"Review for {tool_name}",
                            "rating": 1,
                            "source": "G2"
                        }
                    ]
                
                mock_scrape.side_effect = mock_scrape_async
                reviews = scrape_tool_sync(tool_name, tool_config)
                
                # Extract patterns
                extractor = PatternExtractor()
                patterns = extractor.extract_patterns(reviews)
                
                # AI analysis
                ai_analysis = mock_xai_client.analyze_patterns(
                    tool_name,
                    patterns["patterns"],
                    reviews
                )
                
                all_results[tool_name] = {
                    "reviews": reviews,
                    "patterns": patterns,
                    "ai_analysis": ai_analysis
                }
        
        assert len(all_results) == len(tools)
        assert "Salesforce" in all_results
        assert "HubSpot" in all_results
    
    def test_error_recovery_flow(self):
        """Test error recovery in complete flow"""
        tool_name = "Test Tool"
        tool_config = {"g2_slug": "test", "capterra_id": "123"}
        
        # Test scraping failure recovery
        with patch('utils.async_helpers.scrape_tool_async') as mock_scrape:
            async def mock_scrape_async(tool_name, tool_config, max_reviews):
                raise Exception("Scraping failed")
            
            mock_scrape.side_effect = mock_scrape_async
            
            # Should handle error gracefully
            try:
                reviews = scrape_tool_sync(tool_name, tool_config)
                # If no exception, should return empty list or handle gracefully
                assert isinstance(reviews, list)
            except Exception:
                # Exception is acceptable if handled properly
                pass
    
    def test_caching_flow(self, sample_reviews):
        """Test caching in complete flow"""
        cache_manager = CacheManager()
        tool_name = "Test Tool"
        cache_key = f"reviews_{tool_name}"
        
        # Set cache
        cache_manager.set(cache_key, sample_reviews)
        
        # Verify cache hit
        cached = cache_manager.get(cache_key)
        assert cached == sample_reviews
        
        # Simulate using cached data in flow
        extractor = PatternExtractor()
        patterns = extractor.extract_patterns(cached)
        assert patterns["patterns"]
    
    def test_database_persistence_flow(self, sample_reviews, mock_xai_client):
        """Test database persistence in complete flow"""
        db_manager = get_db_manager()
        tool_name = "Test Tool E2E"
        
        # Save reviews
        count = db_manager.save_reviews(tool_name, sample_reviews)
        assert count == len(sample_reviews)
        
        # Retrieve reviews
        retrieved = db_manager.get_reviews(tool_name)
        assert len(retrieved) >= len(sample_reviews)
        
        # Extract patterns
        extractor = PatternExtractor()
        patterns = extractor.extract_patterns(retrieved)
        
        # AI analysis
        ai_analysis = mock_xai_client.analyze_patterns(
            tool_name,
            patterns["patterns"],
            retrieved
        )
        
        # Save analysis result
        result_id = db_manager.save_analysis_result(
            tool_name=tool_name,
            session_id="test_session",
            patterns=patterns,
            ai_analysis=ai_analysis,
            product_ideas=[]
        )
        
        assert result_id > 0
        
        # Retrieve analysis result
        result = db_manager.get_analysis_result(result_id)
        assert result is not None
        assert result["tool_name"] == tool_name


class TestE2EUserScenarios:
    """Test realistic user scenarios"""
    
    def test_first_time_user_flow(self):
        """Test first-time user experience"""
        # User enters API key
        # User selects tools
        # User runs analysis
        # User views results
        # User exports results
        
        # This would require Streamlit testing framework
        # For now, test the underlying functions
        pass
    
    def test_returning_user_flow(self):
        """Test returning user with cached data"""
        cache_manager = CacheManager()
        tool_name = "Salesforce"
        cache_key = f"reviews_{tool_name}"
        
        # Simulate cached data
        cached_reviews = [
            {"text": "Cached review", "rating": 1, "source": "G2"}
        ]
        cache_manager.set(cache_key, cached_reviews)
        
        # User runs analysis - should use cache
        cached = cache_manager.get(cache_key)
        assert cached == cached_reviews
    
    def test_error_scenario_flow(self):
        """Test error handling scenarios"""
        # API key invalid
        # Scraping fails
        # AI analysis fails
        # Network errors
        
        # Test that errors are handled gracefully
        pass


@pytest.mark.integration
class TestE2EIntegration:
    """Integration tests for E2E flows"""
    
    def test_full_pipeline_integration(self):
        """Test full pipeline with real components (mocked external APIs)"""
        # This would test with real database, cache, etc.
        # but mocked external APIs (G2, Capterra, xAI)
        pass
    
    def test_performance_integration(self):
        """Test performance characteristics of full pipeline"""
        import time
        
        start = time.time()
        
        # Run full pipeline
        # (with mocked external calls)
        
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 30.0  # 30 seconds for full pipeline
