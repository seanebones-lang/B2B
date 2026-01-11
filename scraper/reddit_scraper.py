"""Reddit scraper for product complaints and reviews using PRAW API"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.logging import get_logger
import os

logger = get_logger(__name__)

# Try to import PRAW, fallback to requests if not available
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    import requests


class RedditScraper:
    """Scraper for Reddit complaints and product discussions using PRAW API"""
    
    def __init__(self):
        """Initialize Reddit scraper with PRAW if available"""
        self.use_praw = PRAW_AVAILABLE
        
        if self.use_praw:
            # Initialize PRAW client from environment variables or Streamlit secrets
            try:
                import streamlit as st
                # Try to get from Streamlit secrets first
                try:
                    reddit_config = st.secrets.get("reddit", {})
                    client_id = reddit_config.get("client_id") or os.getenv("REDDIT_CLIENT_ID")
                    client_secret = reddit_config.get("client_secret") or os.getenv("REDDIT_CLIENT_SECRET")
                    user_agent = reddit_config.get("user_agent") or os.getenv("REDDIT_USER_AGENT", "B2BComplaintAnalyzer/1.0")
                except:
                    # Fallback to environment variables
                    client_id = os.getenv("REDDIT_CLIENT_ID")
                    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
                    user_agent = os.getenv("REDDIT_USER_AGENT", "B2BComplaintAnalyzer/1.0")
                
                if client_id and client_secret:
                    self.reddit = praw.Reddit(
                        client_id=client_id,
                        client_secret=client_secret,
                        user_agent=user_agent
                    )
                    logger.info("Reddit scraper initialized with PRAW API")
                else:
                    logger.warning("Reddit credentials not found, falling back to requests")
                    self.use_praw = False
                    self._init_requests()
            except Exception as e:
                logger.warning("Failed to initialize PRAW, falling back to requests", error=str(e))
                self.use_praw = False
                self._init_requests()
        else:
            self._init_requests()
    
    def _init_requests(self):
        """Initialize fallback requests-based scraper"""
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        logger.info("Reddit scraper initialized with requests fallback")
    
    def scrape_product_complaints(
        self,
        tool_name: str,
        max_posts: int = 50,
        subreddits: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape Reddit for product complaints using PRAW API or fallback
        
        Args:
            tool_name: Name of the tool/product
            max_posts: Maximum number of posts to collect
            subreddits: List of subreddits to search (defaults to common ones)
            date_from: Filter posts from this date (ISO format)
            date_to: Filter posts up to this date (ISO format)
            
        Returns:
            List of complaint dictionaries
        """
        if self.use_praw:
            return self._scrape_with_praw(tool_name, max_posts, subreddits, date_from, date_to)
        else:
            return self._scrape_with_requests(tool_name, max_posts, subreddits, date_from, date_to)
    
    def _scrape_with_praw(
        self,
        tool_name: str,
        max_posts: int,
        subreddits: Optional[List[str]],
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Scrape using PRAW API"""
        if not subreddits:
            subreddits = ['saas', 'software', 'productivity', 'startups', 'smallbusiness']
        
        complaints = []
        
        # Use advanced Reddit search operators: "Salesforce complaints site:reddit.com"
        search_query = f"{tool_name} complaints site:reddit.com"
        
        try:
            # Search across Reddit
            for submission in self.reddit.subreddit('all').search(search_query, limit=max_posts, sort='new'):
                if len(complaints) >= max_posts:
                    break
                
                # Date filtering
                if date_from or date_to:
                    post_date = datetime.fromtimestamp(submission.created_utc)
                    if date_from:
                        from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        if post_date < from_date:
                            continue
                    if date_to:
                        to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        if post_date > to_date:
                            continue
                
                # Combine title and text
                full_text = f"{submission.title}\n\n{submission.selftext}".strip()
                
                if len(full_text) < 50:
                    continue
                
                # Check for complaint indicators
                negative_words = ['problem', 'issue', 'bug', 'broken', 'disappointed', 
                                'frustrated', 'terrible', 'awful', 'worst', 'hate',
                                'switching', 'alternative']
                
                if not any(word in full_text.lower() for word in negative_words):
                    continue
                
                rating = 1 if any(word in full_text.lower() for word in ['terrible', 'awful', 'worst', 'hate']) else 2
                
                complaints.append({
                    'text': full_text,
                    'rating': rating,
                    'date': datetime.fromtimestamp(submission.created_utc).isoformat(),
                    'source': f'Reddit (r/{submission.subreddit.display_name})',
                    'tool': tool_name,
                    'metadata': {
                        'score': submission.score,
                        'comments': submission.num_comments,
                        'subreddit': submission.subreddit.display_name
                    }
                })
                
        except Exception as e:
            logger.error("Error scraping Reddit with PRAW", error=str(e))
        
        logger.info("Reddit scraping complete (PRAW)", tool_name=tool_name, complaints_found=len(complaints))
        return complaints
    
    def _scrape_with_requests(
        self,
        tool_name: str,
        max_posts: int,
        subreddits: Optional[List[str]],
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fallback scraping using requests"""
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
                        
                        # Date filtering
                        if date_from or date_to:
                            created = post_data.get('created_utc', 0)
                            post_date = datetime.fromtimestamp(created)
                            if date_from:
                                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                                if post_date < from_date:
                                    continue
                            if date_to:
                                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                                if post_date > to_date:
                                    continue
                        
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
                    
                    # Be polite - rate limiting (1 req/sec)
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error("Error scraping Reddit", error=str(e), subreddit=subreddit, keyword=keyword)
                    continue
        
        logger.info("Reddit scraping complete (requests)", tool_name=tool_name, complaints_found=len(complaints))
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
