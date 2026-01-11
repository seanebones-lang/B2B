"""Hacker News scraper for product discussions and complaints"""

import re
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)


class HackerNewsScraper:
    """Scraper for Hacker News product discussions"""
    
    def __init__(self):
        """Initialize Hacker News scraper"""
        self.base_url = "https://hn.algolia.com/api/v1"
        self.headers = {
            'User-Agent': 'B2B-Complaint-Analyzer'
        }
        logger.info("Hacker News scraper initialized")
    
    def scrape_discussions(
        self,
        tool_name: str,
        max_items: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape Hacker News for product discussions
        
        Args:
            tool_name: Name of the tool/product
            max_items: Maximum number of items to collect
            
        Returns:
            List of discussion dictionaries
        """
        discussions = []
        
        # Search queries
        search_queries = [
            f"{tool_name} alternative",
            f"{tool_name} vs",
            f"{tool_name} problem",
            f"{tool_name} issue",
            f"switching from {tool_name}",
        ]
        
        for query in search_queries:
            if len(discussions) >= max_items:
                break
            
            try:
                # Search using Algolia HN API
                search_url = f"{self.base_url}/search"
                params = {
                    'query': query,
                    'tags': 'comment',  # Focus on comments
                    'hitsPerPage': 20
                }
                
                response = requests.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.warning("HN API request failed", status=response.status_code)
                    continue
                
                data = response.json()
                hits = data.get('hits', [])
                
                for hit in hits:
                    if len(discussions) >= max_items:
                        break
                    
                    comment_text = hit.get('comment_text', '')
                    if not comment_text:
                        continue
                    
                    # Remove HTML tags
                    from bs4 import BeautifulSoup
                    clean_text = BeautifulSoup(comment_text, 'html.parser').get_text()
                    
                    # Filter short comments
                    if len(clean_text) < 50:
                        continue
                    
                    # Check for negative sentiment
                    negative_words = ['problem', 'issue', 'disappointed', 'frustrat', 
                                    'terrible', 'awful', 'switching', 'alternative', 
                                    'better than', 'worse', 'lacking']
                    
                    if not any(word in clean_text.lower() for word in negative_words):
                        continue
                    
                    created_at = hit.get('created_at', '')
                    points = hit.get('points', 0)
                    story_title = hit.get('story_title', '')
                    
                    # Estimate rating
                    very_negative = ['terrible', 'awful', 'worst', 'hate']
                    rating = 1 if any(word in clean_text.lower() for word in very_negative) else 2
                    
                    discussions.append({
                        'text': clean_text,
                        'rating': rating,
                        'date': created_at,
                        'source': 'Hacker News',
                        'tool': tool_name,
                        'metadata': {
                            'points': points,
                            'story_title': story_title,
                            'url': hit.get('story_url', '')
                        }
                    })
                
                # Rate limiting
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error("Error scraping Hacker News", error=str(e), query=query)
                continue
        
        logger.info("Hacker News scraping complete", 
                   tool_name=tool_name, 
                   discussions_found=len(discussions))
        
        return discussions
