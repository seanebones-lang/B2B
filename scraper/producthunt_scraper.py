"""Product Hunt scraper for product comments and reviews"""

import re
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from utils.logging import get_logger

logger = get_logger(__name__)


class ProductHuntScraper:
    """Scraper for Product Hunt comments and reviews"""
    
    def __init__(self):
        """Initialize Product Hunt scraper"""
        self.base_url = "https://www.producthunt.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        logger.info("Product Hunt scraper initialized")
    
    def scrape_product_comments(
        self,
        tool_name: str,
        product_slug: Optional[str] = None,
        max_comments: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape Product Hunt for product comments
        
        Args:
            tool_name: Name of the tool/product
            product_slug: Product Hunt slug (e.g., 'notion-2-0')
            max_comments: Maximum number of comments to collect
            
        Returns:
            List of comment dictionaries
        """
        if not product_slug:
            # Try to find product by search
            product_slug = self._find_product_slug(tool_name)
            if not product_slug:
                logger.warning("Could not find Product Hunt page", tool_name=tool_name)
                return []
        
        comments = []
        
        try:
            # Get product page
            product_url = f"{self.base_url}/posts/{product_slug}"
            
            response = requests.get(
                product_url,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code != 200:
                logger.warning("Product Hunt page not found", status=response.status_code, slug=product_slug)
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find comment elements (structure may vary)
            comment_elements = soup.find_all('div', class_=re.compile(r'comment|review'))
            
            for comment_elem in comment_elements:
                if len(comments) >= max_comments:
                    break
                
                # Extract comment text
                text_elem = comment_elem.find('p') or comment_elem.find('div', class_=re.compile(r'text|content'))
                if not text_elem:
                    continue
                
                comment_text = text_elem.get_text(strip=True)
                
                # Filter short comments
                if len(comment_text) < 30:
                    continue
                
                # Look for critical/negative comments
                negative_indicators = ['problem', 'issue', 'disappointed', 'lacking', 
                                     'missing', 'wish', 'needs', 'could be better',
                                     'unfortunately', 'however', 'but']
                
                has_criticism = any(indicator in comment_text.lower() for indicator in negative_indicators)
                
                if has_criticism:
                    # Extract author
                    author_elem = comment_elem.find('a', class_=re.compile(r'user|author'))
                    author = author_elem.get_text(strip=True) if author_elem else 'Anonymous'
                    
                    # Estimate rating based on sentiment
                    very_negative = ['terrible', 'awful', 'worst', 'disappointed']
                    rating = 1 if any(word in comment_text.lower() for word in very_negative) else 2
                    
                    comments.append({
                        'text': comment_text,
                        'rating': rating,
                        'date': datetime.now().isoformat(),
                        'source': 'Product Hunt',
                        'tool': tool_name,
                        'metadata': {
                            'author': author,
                            'product_slug': product_slug
                        }
                    })
            
            logger.info("Product Hunt scraping complete", 
                       tool_name=tool_name, 
                       comments_found=len(comments))
            
        except Exception as e:
            logger.error("Error scraping Product Hunt", error=str(e), tool_name=tool_name)
        
        return comments
    
    def _find_product_slug(self, tool_name: str) -> Optional[str]:
        """
        Find Product Hunt slug by searching
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Product slug or None
        """
        try:
            search_url = f"{self.base_url}/search"
            params = {'q': tool_name}
            
            response = requests.get(
                search_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find first product link
            product_link = soup.find('a', href=re.compile(r'/posts/[a-z0-9-]+'))
            if product_link:
                href = product_link.get('href', '')
                match = re.search(r'/posts/([a-z0-9-]+)', href)
                if match:
                    return match.group(1)
            
        except Exception as e:
            logger.error("Error finding product slug", error=str(e), tool_name=tool_name)
        
        return None
