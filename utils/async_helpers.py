"""Async helper utilities for Streamlit integration"""

import asyncio
from typing import List, Dict, Any, Optional
from functools import wraps

from scraper.g2_scraper_async import G2ScraperAsync
from scraper.capterra_scraper_async import CapterraScraperAsync
from utils.logging import get_logger
from utils.monitoring import monitor_performance_async
import config

logger = get_logger(__name__)


def run_async(coro):
    """
    Run async coroutine in sync context (for Streamlit)
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result of coroutine
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


async def scrape_tool_async(
    tool_name: str,
    tool_config: Dict[str, Any],
    max_reviews: int = 30
) -> List[Dict[str, Any]]:
    """
    Scrape reviews for a tool using async scrapers (parallel)
    
    Args:
        tool_name: Name of the tool
        tool_config: Tool configuration dictionary
        max_reviews: Maximum reviews per source
        
    Returns:
        List of review dictionaries
    """
    reviews = []
    
    async def scrape_g2():
        """Scrape G2 reviews"""
        try:
            async with G2ScraperAsync() as scraper:
                return await scraper.scrape_reviews(
                    tool_name,
                    tool_slug=tool_config.get("g2_slug"),
                    max_reviews=max_reviews
                )
        except Exception as e:
            logger.error("G2 async scraping failed", tool_name=tool_name, error=str(e))
            return []
    
    async def scrape_capterra():
        """Scrape Capterra reviews"""
        try:
            async with CapterraScraperAsync() as scraper:
                return await scraper.scrape_reviews(
                    tool_name,
                    tool_id=tool_config.get("capterra_id"),
                    max_reviews=max_reviews
                )
        except Exception as e:
            logger.error("Capterra async scraping failed", tool_name=tool_name, error=str(e))
            return []
    
    # Scrape both sources in parallel
    try:
        g2_reviews, capterra_reviews = await asyncio.gather(
            scrape_g2(),
            scrape_capterra(),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(g2_reviews, Exception):
            logger.error("G2 scraping exception", tool_name=tool_name, error=str(g2_reviews))
            g2_reviews = []
        if isinstance(capterra_reviews, Exception):
            logger.error("Capterra scraping exception", tool_name=tool_name, error=str(capterra_reviews))
            capterra_reviews = []
        
        reviews.extend(g2_reviews if isinstance(g2_reviews, list) else [])
        reviews.extend(capterra_reviews if isinstance(capterra_reviews, list) else [])
        
        logger.info(
            "Async scraping complete",
            tool_name=tool_name,
            g2_count=len(g2_reviews) if isinstance(g2_reviews, list) else 0,
            capterra_count=len(capterra_reviews) if isinstance(capterra_reviews, list) else 0,
            total=len(reviews)
        )
        
    except Exception as e:
        logger.error("Async scraping failed", tool_name=tool_name, error=str(e))
    
    return reviews


async def scrape_multiple_tools_async(
    tools: List[Dict[str, Any]],
    max_reviews_per_tool: int = 30,
    max_concurrent: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scrape multiple tools in parallel with concurrency limit
    
    Args:
        tools: List of tool dictionaries with name and config
        max_reviews_per_tool: Maximum reviews per tool
        max_concurrent: Maximum concurrent scraping operations
        
    Returns:
        Dictionary mapping tool names to review lists
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def scrape_with_semaphore(tool_name: str, tool_config: Dict[str, Any]):
        """Scrape with semaphore for concurrency control"""
        async with semaphore:
            return tool_name, await scrape_tool_async(tool_name, tool_config, max_reviews_per_tool)
    
    # Create tasks for all tools
    tasks = [
        scrape_with_semaphore(tool["name"], tool)
        for tool in tools
    ]
    
    # Execute all tasks
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in completed:
        if isinstance(result, Exception):
            logger.error("Tool scraping exception", error=str(result))
            continue
        
        tool_name, reviews = result
        results[tool_name] = reviews
    
    return results


def scrape_tool_sync(
    tool_name: str,
    tool_config: Dict[str, Any],
    max_reviews: int = 30
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for async scraping (for Streamlit compatibility)
    
    Args:
        tool_name: Name of the tool
        tool_config: Tool configuration dictionary
        max_reviews: Maximum reviews per source
        
    Returns:
        List of review dictionaries
    """
    return run_async(scrape_tool_async(tool_name, tool_config, max_reviews))
