"""Google News scraper via SerpAPI for B2B product complaints"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)

# Try to import serpapi
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    logger.warning("serpapi not available. Install with: pip install google-search-results")


class GoogleNewsScraper:
    """Scraper for Google News articles about B2B products"""
    
    def __init__(self):
        """Initialize Google News scraper"""
        self.api_key = None
        
        # Try to get API key from Streamlit secrets or environment
        try:
            import streamlit as st
            serpapi_config = st.secrets.get("serpapi", {})
            self.api_key = serpapi_config.get("api_key") or None
        except:
            import os
            self.api_key = os.getenv("SERPAPI_API_KEY")
        
        if not self.api_key and SERPAPI_AVAILABLE:
            logger.warning("SerpAPI key not found. Add to Streamlit secrets or set SERPAPI_API_KEY env var")
        
        logger.info("Google News scraper initialized", has_api_key=bool(self.api_key))
    
    def scrape_product_news(
        self,
        tool_name: str,
        max_articles: int = 50,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape Google News for articles about product complaints
        
        Args:
            tool_name: Name of the tool/product
            max_articles: Maximum number of articles to collect
            date_from: Filter articles from this date (ISO format)
            date_to: Filter articles up to this date (ISO format)
            
        Returns:
            List of complaint dictionaries
            
        Note:
            Requires SerpAPI key ($50/month). Add to Streamlit secrets:
            serpapi:
              api_key: your_api_key
        """
        if not SERPAPI_AVAILABLE or not self.api_key:
            logger.warning("SerpAPI not available or API key missing")
            return []
        
        complaints = []
        
        try:
            # Search queries for complaints
            search_queries = [
                f"{tool_name} problems",
                f"{tool_name} issues",
                f"{tool_name} complaints",
                f"{tool_name} alternatives",
            ]
            
            for query in search_queries:
                if len(complaints) >= max_articles:
                    break
                
                params = {
                    "q": query,
                    "tbm": "nws",  # News search
                    "api_key": self.api_key,
                    "num": 20  # Results per page
                }
                
                # Add date filters if provided
                if date_from:
                    params["tbs"] = f"cdr:1,cd_min:{date_from},cd_max:{date_to or datetime.now().strftime('%Y-%m-%d')}"
                
                search = GoogleSearch(params)
                results = search.get_dict()
                
                news_results = results.get("news_results", [])
                
                for article in news_results:
                    if len(complaints) >= max_articles:
                        break
                    
                    title = article.get("title", "")
                    snippet = article.get("snippet", "")
                    link = article.get("link", "")
                    date = article.get("date", "")
                    
                    # Combine title and snippet
                    full_text = f"{title}\n\n{snippet}".strip()
                    
                    if len(full_text) < 50:
                        continue
                    
                    # Check for complaint indicators
                    negative_words = ['problem', 'issue', 'bug', 'broken', 'disappointed',
                                    'frustrated', 'terrible', 'awful', 'worst', 'hate',
                                    'switching', 'alternative', 'complaint']
                    
                    if not any(word in full_text.lower() for word in negative_words):
                        continue
                    
                    rating = 1 if any(word in full_text.lower() for word in ['terrible', 'awful', 'worst', 'hate']) else 2
                    
                    complaints.append({
                        'text': full_text,
                        'rating': rating,
                        'date': date or datetime.now().isoformat(),
                        'source': 'Google News',
                        'tool': tool_name,
                        'metadata': {
                            'link': link,
                            'query': query
                        }
                    })
                
                # Rate limiting (SerpAPI has rate limits)
                import time
                time.sleep(1)
                
        except Exception as e:
            logger.error("Error scraping Google News", error=str(e))
        
        logger.info("Google News scraping complete", tool_name=tool_name, articles_found=len(complaints))
        return complaints
