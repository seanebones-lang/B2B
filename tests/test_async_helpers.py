"""Tests for async helper utilities"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from utils.async_helpers import (
    run_async,
    scrape_tool_async,
    scrape_tool_sync,
    scrape_multiple_tools_async
)


class TestAsyncHelpers:
    """Test async helper functions"""
    
    @pytest.mark.asyncio
    async def test_run_async(self):
        """Test run_async wrapper"""
        async def test_coro():
            return "test_result"
        
        result = run_async(test_coro())
        assert result == "test_result"
    
    @pytest.mark.asyncio
    async def test_scrape_tool_async(self):
        """Test async tool scraping"""
        tool_config = {
            "g2_slug": "test-tool",
            "capterra_id": "123"
        }
        
        with patch('utils.async_helpers.G2ScraperAsync') as mock_g2, \
             patch('utils.async_helpers.CapterraScraperAsync') as mock_capterra:
            
            # Mock async context managers
            mock_g2_instance = AsyncMock()
            mock_g2_instance.scrape_reviews = AsyncMock(return_value=[
                {"text": "G2 review", "rating": 1, "source": "G2"}
            ])
            mock_g2.return_value.__aenter__ = AsyncMock(return_value=mock_g2_instance)
            mock_g2.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_capterra_instance = AsyncMock()
            mock_capterra_instance.scrape_reviews = AsyncMock(return_value=[
                {"text": "Capterra review", "rating": 2, "source": "Capterra"}
            ])
            mock_capterra.return_value.__aenter__ = AsyncMock(return_value=mock_capterra_instance)
            mock_capterra.return_value.__aexit__ = AsyncMock(return_value=None)
            
            reviews = await scrape_tool_async("Test Tool", tool_config, max_reviews=10)
            
            assert len(reviews) == 2
            assert reviews[0]["source"] == "G2"
            assert reviews[1]["source"] == "Capterra"
    
    def test_scrape_tool_sync(self):
        """Test synchronous wrapper"""
        tool_config = {
            "g2_slug": "test-tool",
            "capterra_id": "123"
        }
        
        with patch('utils.async_helpers.scrape_tool_async') as mock_async:
            mock_async.return_value = asyncio.coroutine(lambda: [
                {"text": "Review", "rating": 1, "source": "G2"}
            ])()
            
            # Mock the async function to return a coroutine
            async def mock_scrape():
                return [{"text": "Review", "rating": 1, "source": "G2"}]
            
            with patch('utils.async_helpers.scrape_tool_async', side_effect=mock_scrape):
                reviews = scrape_tool_sync("Test Tool", tool_config)
                assert isinstance(reviews, list)
    
    @pytest.mark.asyncio
    async def test_scrape_multiple_tools_async(self):
        """Test parallel scraping of multiple tools"""
        tools = [
            {"name": "Tool1", "g2_slug": "tool1", "capterra_id": "1"},
            {"name": "Tool2", "g2_slug": "tool2", "capterra_id": "2"}
        ]
        
        with patch('utils.async_helpers.scrape_tool_async') as mock_scrape:
            async def mock_scrape_side_effect(tool_name, tool_config, max_reviews):
                return [{"text": f"{tool_name} review", "rating": 1, "source": "G2"}]
            
            mock_scrape.side_effect = mock_scrape_side_effect
            
            results = await scrape_multiple_tools_async(tools, max_reviews_per_tool=10)
            
            assert "Tool1" in results
            assert "Tool2" in results
            assert len(results["Tool1"]) == 1
            assert len(results["Tool2"]) == 1
