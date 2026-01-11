"""LinkedIn scraper for B2B groups and discussions"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logging import get_logger
import requests
from bs4 import BeautifulSoup

logger = get_logger(__name__)


class LinkedInScraper:
    """Scraper for LinkedIn B2B groups and discussions"""
    
    def __init__(self):
        """Initialize LinkedIn scraper"""
        self.base_url = "https://www.linkedin.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        logger.info("LinkedIn scraper initialized")
    
    def scrape_b2b_complaints(
        self,
        tool_name: str,
        max_posts: int = 50,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape LinkedIn for B2B complaints and discussions
        
        Args:
            tool_name: Name of the tool/product
            max_posts: Maximum number of posts to collect
            date_from: Filter posts from this date (ISO format)
            date_to: Filter posts up to this date (ISO format)
            
        Returns:
            List of complaint dictionaries
            
        Note:
            LinkedIn requires authentication for most content. This is a basic implementation
            that searches public posts. For production, use LinkedIn API with OAuth.
        """
        complaints = []
        
        # Search for B2B groups related to the tool
        # Example: "Salesforce admins complaints" or "HubSpot users"
        search_queries = [
            f"{tool_name} admins complaints",
            f"{tool_name} users problems",
            f"{tool_name} issues",
            f"switching from {tool_name}",
        ]
        
        for query in search_queries:
            if len(complaints) >= max_posts:
                break
            
            try:
                # LinkedIn search URL (public posts)
                # Note: LinkedIn heavily restricts scraping. For production, use LinkedIn API
                search_url = f"{self.base_url}/search/results/content/"
                params = {
                    'keywords': query,
                    'origin': 'GLOBAL_SEARCH_HEADER'
                }
                
                response = requests.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.warning("LinkedIn request failed", status=response.status_code, query=query)
                    continue
                
                # Parse HTML (LinkedIn uses dynamic content, so this is limited)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find post elements (LinkedIn structure may vary)
                post_elements = soup.find_all('div', class_='feed-shared-update-v2')
                
                for post_elem in post_elements:
                    if len(complaints) >= max_posts:
                        break
                    
                    # Extract post text
                    text_elem = post_elem.find('span', class_='feed-shared-text')
                    if not text_elem:
                        continue
                    
                    post_text = text_elem.get_text(strip=True)
                    
                    if len(post_text) < 50:
                        continue
                    
                    # Check for complaint indicators
                    negative_words = ['problem', 'issue', 'bug', 'broken', 'disappointed',
                                    'frustrated', 'terrible', 'awful', 'worst', 'hate',
                                    'switching', 'alternative']
                    
                    if not any(word in post_text.lower() for word in negative_words):
                        continue
                    
                    # Extract date if available
                    date_elem = post_elem.find('time')
                    date = date_elem.get('datetime', '') if date_elem else datetime.now().isoformat()
                    
                    # Date filtering
                    if date_from or date_to:
                        try:
                            post_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                            if date_from:
                                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                                if post_date < from_date:
                                    continue
                            if date_to:
                                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                                if post_date > to_date:
                                    continue
                        except:
                            pass
                    
                    rating = 1 if any(word in post_text.lower() for word in ['terrible', 'awful', 'worst', 'hate']) else 2
                    
                    complaints.append({
                        'text': post_text,
                        'rating': rating,
                        'date': date,
                        'source': 'LinkedIn',
                        'tool': tool_name,
                        'metadata': {
                            'query': query
                        }
                    })
                
                # Rate limiting (1 req/sec)
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error("Error scraping LinkedIn", error=str(e), query=query)
                continue
        
        logger.info("LinkedIn scraping complete", tool_name=tool_name, complaints_found=len(complaints))
        return complaints
