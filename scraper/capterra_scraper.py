"""Capterra.com review scraper"""

from bs4 import BeautifulSoup
from .base import BaseScraper
import re


class CapterraScraper(BaseScraper):
    """Scraper for Capterra.com reviews"""
    
    def scrape_reviews(self, tool_name, tool_slug=None, tool_id=None, max_reviews=30):
        """
        Scrape 1-2 star reviews from Capterra
        URL pattern: https://www.capterra.com/p/{id}/{tool}/reviews/?rating=1-2&sort=most_recent
        """
        if not tool_id:
            # Try to find tool ID from tool name search
            search_url = f"https://www.capterra.com/search/{tool_name.replace(' ', '%20')}"
            try:
                response = self._fetch(search_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                # Look for product link
                product_link = soup.find('a', href=re.compile(r'/p/\d+/'))
                if product_link:
                    match = re.search(r'/p/(\d+)/', product_link.get('href', ''))
                    if match:
                        tool_id = match.group(1)
            except:
                pass
        
        if not tool_id:
            # Fallback: try common ID patterns or return empty
            return []
        
        reviews = []
        page = 1
        
        while len(reviews) < max_reviews:
            url = f"https://www.capterra.com/p/{tool_id}/{tool_name.lower().replace(' ', '-')}/reviews/"
            params = {
                "rating": "1-2",
                "sort": "most_recent",
                "page": str(page)
            }
            
            try:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                full_url = f"{url}?{param_str}"
                
                response = self._fetch(full_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review elements (Capterra structure)
                review_elements = soup.find_all(['div', 'article'], class_=re.compile(r'review|rating|comment', re.I))
                
                if not review_elements:
                    # Try alternative selectors
                    review_elements = soup.find_all('div', {'data-testid': re.compile(r'review', re.I)})
                
                if not review_elements:
                    break
                
                for element in review_elements:
                    if len(reviews) >= max_reviews:
                        break
                    
                    # Extract review text
                    text_elem = element.find(['p', 'div'], class_=re.compile(r'text|content|review-text|body|comment', re.I))
                    if not text_elem:
                        text_elem = element.find('p')
                    
                    review_text = text_elem.get_text(strip=True) if text_elem else ""
                    
                    if not review_text or len(review_text) < 20:
                        continue
                    
                    # Extract rating
                    rating_elem = element.find(['span', 'div'], class_=re.compile(r'rating|star', re.I))
                    rating = None
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        rating_match = re.search(r'(\d+)', rating_text)
                        if rating_match:
                            rating = int(rating_match.group(1))
                    
                    # Extract date
                    date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time', re.I))
                    date = None
                    if date_elem:
                        date = date_elem.get_text(strip=True)
                    
                    # Only include 1-2 star reviews
                    if rating and rating <= 2:
                        reviews.append({
                            "text": review_text,
                            "rating": rating,
                            "date": date,
                            "source": "Capterra"
                        })
                
                # Check for next page
                next_page = soup.find('a', {'aria-label': re.compile(r'next|page', re.I)})
                if not next_page or page >= 10:
                    break
                
                page += 1
                
            except Exception as e:
                print(f"Error scraping Capterra page {page} for {tool_name}: {str(e)}")
                break
        
        return reviews[:max_reviews]
