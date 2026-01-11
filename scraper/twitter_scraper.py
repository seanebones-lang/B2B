"""Twitter/X scraper for product mentions and complaints"""

import re
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)


class TwitterScraper:
    """Scraper for Twitter/X product mentions (using nitter.net as proxy)"""
    
    def __init__(self):
        """Initialize Twitter scraper"""
        # Use Nitter instances (Twitter frontend proxy)
        self.nitter_instances = [
            'https://nitter.net',
            'https://nitter.1d4.us',
            'https://nitter.kavin.rocks',
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        logger.info("Twitter scraper initialized")
    
    def _get_working_instance(self) -> Optional[str]:
        """Find a working Nitter instance"""
        for instance in self.nitter_instances:
            try:
                response = requests.get(instance, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    return instance
            except:
                continue
        return None
    
    def scrape_product_mentions(
        self,
        tool_name: str,
        max_tweets: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape Twitter for product complaints and mentions
        
        Args:
            tool_name: Name of the tool/product
            max_tweets: Maximum number of tweets to collect
            
        Returns:
            List of complaint dictionaries
        """
        complaints = []
        
        # Get working Nitter instance
        nitter_url = self._get_working_instance()
        if not nitter_url:
            logger.warning("No working Nitter instance found")
            return []
        
        # Search queries for complaints
        search_queries = [
            f"{tool_name} problem",
            f"{tool_name} issue",
            f"{tool_name} broken",
            f"{tool_name} disappointed",
            f"{tool_name} switching",
        ]
        
        for query in search_queries:
            if len(complaints) >= max_tweets:
                break
            
            try:
                # Nitter search URL
                search_url = f"{nitter_url}/search"
                params = {
                    'f': 'tweets',
                    'q': query,
                    'since': '',
                    'until': '',
                    'near': ''
                }
                
                response = requests.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                
                if response.status_code != 200:
                    logger.warning("Twitter search failed", status=response.status_code, query=query)
                    continue
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find tweet elements
                tweet_elements = soup.find_all('div', class_='timeline-item')
                
                for tweet_elem in tweet_elements:
                    if len(complaints) >= max_tweets:
                        break
                    
                    # Extract tweet text
                    tweet_content = tweet_elem.find('div', class_='tweet-content')
                    if not tweet_content:
                        continue
                    
                    tweet_text = tweet_content.get_text(strip=True)
                    
                    # Filter short tweets
                    if len(tweet_text) < 30:
                        continue
                    
                    # Extract date
                    date_elem = tweet_elem.find('span', class_='tweet-date')
                    date = date_elem.get('title', '') if date_elem else ''
                    
                    # Extract engagement metrics
                    stats_elem = tweet_elem.find('div', class_='tweet-stats')
                    engagement = 0
                    if stats_elem:
                        # Count retweets, likes, etc.
                        stat_items = stats_elem.find_all('span', class_='tweet-stat')
                        for stat in stat_items:
                            try:
                                engagement += int(stat.get_text(strip=True))
                            except:
                                pass
                    
                    # Determine sentiment/rating
                    very_negative = ['terrible', 'awful', 'worst', 'hate', 'garbage']
                    rating = 1 if any(word in tweet_text.lower() for word in very_negative) else 2
                    
                    complaints.append({
                        'text': tweet_text,
                        'rating': rating,
                        'date': date,
                        'source': 'Twitter',
                        'tool': tool_name,
                        'metadata': {
                            'engagement': engagement,
                            'query': query
                        }
                    })
                
                # Rate limiting
                import time
                time.sleep(3)
                
            except Exception as e:
                logger.error("Error scraping Twitter", error=str(e), query=query)
                continue
        
        logger.info("Twitter scraping complete", tool_name=tool_name, mentions_found=len(complaints))
        return complaints
