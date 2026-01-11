"""Reddit scraper for product complaints and reviews"""

import re
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from utils.logging import get_logger

logger = get_logger(__name__)


class RedditScraper:
    """Scraper for Reddit complaints and product discussions"""
    
    def __init__(self):
        """Initialize Reddit scraper"""
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        logger.info("Reddit scraper initialized")
    
    def scrape_product_complaints(
        self,
        tool_name: str,
        max_posts: int = 50,
        subreddits: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape Reddit for product complaints
        
        Args:
            tool_name: Name of the tool/product
            max_posts: Maximum number of posts to collect
            subreddits: List of subreddits to search (defaults to common ones)
            
        Returns:
            List of complaint dictionaries
        """
        if not subreddits:
            subreddits = ['saas', 'software', 'productivity', 'startups', 'smallbusiness']
        
        complaints = []
        
        # Search terms for complaints
        complaint_keywords = [
            f"{tool_name} problem",
            f"{tool_name} issue",
            f"{tool_name} complaint",
            f"{tool_name} disappointed",
            f"{tool_name} frustrated",
            f"{tool_name} alternative",
            f"switching from {tool_name}"
        ]
        
        for subreddit in subreddits:
            if len(complaints) >= max_posts:
                break
            
            for keyword in complaint_keywords:
                if len(complaints) >= max_posts:
                    break
                
                try:
                    # Use Reddit JSON API
                    search_url = f"{self.base_url}/r/{subreddit}/search.json"
                    params = {
                        'q': keyword,
                        'restrict_sr': 'on',
                        'sort': 'new',
                        'limit': 25
                    }
                    
                    response = requests.get(
                        search_url,
                        headers=self.headers,
                        params=params,
                        timeout=10
                    )
                    
                    if response.status_code != 200:
                        logger.warning("Reddit request failed", status=response.status_code, subreddit=subreddit)
                        continue
                    
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        if len(complaints) >= max_posts:
                            break
                        
                        post_data = post.get('data', {})
                        
                        # Extract post content
                        title = post_data.get('title', '')
                        selftext = post_data.get('selftext', '')
                        score = post_data.get('score', 0)
                        created = post_data.get('created_utc', 0)
                        num_comments = post_data.get('num_comments', 0)
                        
                        # Combine title and text
                        full_text = f"{title}\n\n{selftext}".strip()
                        
                        # Filter out short or irrelevant posts
                        if len(full_text) < 50:
                            continue
                        
                        # Check if it's actually a complaint (negative sentiment indicators)
                        negative_words = ['problem', 'issue', 'bug', 'broken', 'disappointed', 
                                        'frustrated', 'terrible', 'awful', 'worst', 'hate',
                                        'switching', 'alternative', 'better than']
                        
                        if not any(word in full_text.lower() for word in negative_words):
                            continue
                        
                        # Estimate rating based on sentiment (1-2 for complaints)
                        rating = 1 if any(word in full_text.lower() for word in ['terrible', 'awful', 'worst', 'hate']) else 2
                        
                        complaints.append({
                            'text': full_text,
                            'rating': rating,
                            'date': datetime.fromtimestamp(created).isoformat(),
                            'source': f'Reddit (r/{subreddit})',
                            'tool': tool_name,
                            'metadata': {
                                'score': score,
                                'comments': num_comments,
                                'subreddit': subreddit
                            }
                        })
                    
                    # Be polite - rate limiting
                    import time
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error("Error scraping Reddit", error=str(e), subreddit=subreddit, keyword=keyword)
                    continue
        
        logger.info("Reddit scraping complete", tool_name=tool_name, complaints_found=len(complaints))
        return complaints
    
    def scrape_product_subreddit(
        self,
        tool_name: str,
        subreddit_name: Optional[str] = None,
        max_posts: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape a product-specific subreddit for complaints
        
        Args:
            tool_name: Name of the tool
            subreddit_name: Specific subreddit (e.g., 'salesforce', 'hubspot')
            max_posts: Maximum posts to collect
            
        Returns:
            List of complaint dictionaries
        """
        if not subreddit_name:
            # Try to guess subreddit name
            subreddit_name = tool_name.lower().replace(" ", "")
        
        complaints = []
        
        try:
            # Get posts from subreddit
            url = f"{self.base_url}/r/{subreddit_name}/new.json"
            params = {'limit': max_posts}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning("Subreddit not found or inaccessible", subreddit=subreddit_name)
                return []
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                post_data = post.get('data', {})
                
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                score = post_data.get('score', 0)
                created = post_data.get('created_utc', 0)
                
                full_text = f"{title}\n\n{selftext}".strip()
                
                # Look for complaint indicators
                if len(full_text) < 50:
                    continue
                
                # Check for negative sentiment
                negative_indicators = ['problem', 'issue', 'bug', 'help', 'not working', 
                                     'error', 'frustrated', 'disappointed']
                
                if any(indicator in full_text.lower() for indicator in negative_indicators):
                    complaints.append({
                        'text': full_text,
                        'rating': 2,  # Moderate complaint
                        'date': datetime.fromtimestamp(created).isoformat(),
                        'source': f'Reddit (r/{subreddit_name})',
                        'tool': tool_name,
                        'metadata': {
                            'score': score,
                            'subreddit': subreddit_name
                        }
                    })
            
            logger.info("Product subreddit scraping complete", 
                       subreddit=subreddit_name, 
                       complaints_found=len(complaints))
            
        except Exception as e:
            logger.error("Error scraping product subreddit", error=str(e), subreddit=subreddit_name)
        
        return complaints
