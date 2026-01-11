"""Trustpilot scraper for business reviews"""

import re
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)


class TrustpilotScraper:
    """Scraper for Trustpilot reviews"""
    
    def __init__(self):
        """Initialize Trustpilot scraper"""
        self.base_url = "https://www.trustpilot.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        logger.info("Trustpilot scraper initialized")
    
    def scrape_reviews(
        self,
        tool_name: str,
        company_slug: Optional[str] = None,
        max_reviews: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape Trustpilot reviews
        
        Args:
            tool_name: Name of the tool/company
            company_slug: Trustpilot company slug
            max_reviews: Maximum number of reviews to collect
            
        Returns:
            List of review dictionaries
        """
        if not company_slug:
            # Try to find company
            company_slug = self._find_company(tool_name)
            if not company_slug:
                logger.warning("Could not find Trustpilot page", tool_name=tool_name)
                return []
        
        reviews = []
        page = 1
        
        try:
            while len(reviews) < max_reviews:
                url = f"{self.base_url}/review/{company_slug}"
                params = {'page': page, 'stars': '1,2'}  # Only 1-2 star reviews
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                
                if response.status_code != 200:
                    logger.warning("Trustpilot request failed", status=response.status_code)
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review cards
                review_cards = soup.find_all('article', class_=re.compile(r'review'))
                
                if not review_cards:
                    break
                
                for card in review_cards:
                    if len(reviews) >= max_reviews:
                        break
                    
                    # Extract review text
                    text_elem = card.find('p', class_=re.compile(r'review-content'))
                    if not text_elem:
                        continue
                    
                    review_text = text_elem.get_text(strip=True)
                    
                    # Extract rating
                    rating_elem = card.find('div', class_=re.compile(r'star-rating'))
                    rating = 1  # Default
                    if rating_elem:
                        rating_img = rating_elem.find('img')
                        if rating_img and 'alt' in rating_img.attrs:
                            try:
                                rating = int(rating_img['alt'].split()[0])
                            except:
                                pass
                    
                    # Extract date
                    date_elem = card.find('time')
                    date = date_elem.get('datetime', '') if date_elem else ''
                    
                    # Extract title
                    title_elem = card.find('h2', class_=re.compile(r'review-title'))
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    full_text = f"{title}\n\n{review_text}".strip() if title else review_text
                    
                    if len(full_text) < 30:
                        continue
                    
                    reviews.append({
                        'text': full_text,
                        'rating': rating,
                        'date': date,
                        'source': 'Trustpilot',
                        'tool': tool_name,
                        'metadata': {
                            'company_slug': company_slug
                        }
                    })
                
                page += 1
                
                # Rate limiting
                import time
                time.sleep(2)
            
            logger.info("Trustpilot scraping complete", 
                       tool_name=tool_name, 
                       reviews_found=len(reviews))
            
        except Exception as e:
            logger.error("Error scraping Trustpilot", error=str(e), tool_name=tool_name)
        
        return reviews
    
    def _find_company(self, tool_name: str) -> Optional[str]:
        """Find company slug by search"""
        try:
            search_url = f"{self.base_url}/search"
            params = {'query': tool_name}
            
            response = requests.get(
                search_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find first company link
            company_link = soup.find('a', href=re.compile(r'/review/[a-z0-9\-\.]+'))
            if company_link:
                href = company_link.get('href', '')
                match = re.search(r'/review/([a-z0-9\-\.]+)', href)
                if match:
                    return match.group(1)
            
        except Exception as e:
            logger.error("Error finding company", error=str(e), tool_name=tool_name)
        
        return None
