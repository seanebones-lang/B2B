"""G2.com review scraper"""

from bs4 import BeautifulSoup
from .base import BaseScraper
import re


class G2Scraper(BaseScraper):
    """Scraper for G2.com reviews"""
    
    def scrape_reviews(self, tool_name, tool_slug=None, tool_id=None, max_reviews=30):
        """
        Scrape 1-2 star reviews from G2.com
        URL pattern: https://www.g2.com/products/{tool_slug}/reviews?rating=1&rating=2&sort=newest
        """
        if not tool_slug:
            # Convert tool name to slug format
            tool_slug = tool_name.lower().replace(" ", "-")
        
        reviews = []
        page = 1
        
        while len(reviews) < max_reviews:
            url = f"https://www.g2.com/products/{tool_slug}/reviews"
            params = {
                "rating": ["1", "2"],
                "sort": "newest",
                "page": str(page)
            }
            
            try:
                # Build URL with params
                param_str = "&".join([f"{k}={v}" if not isinstance(v, list) else "&".join([f"{k}={item}" for item in v]) for k, v in params.items()])
                full_url = f"{url}?{param_str}"
                
                response = self._fetch(full_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review elements (G2 structure may vary)
                review_elements = soup.find_all(['div', 'article'], class_=re.compile(r'review|rating', re.I))
                
                if not review_elements:
                    # Try alternative selectors
                    review_elements = soup.find_all('div', {'data-testid': re.compile(r'review', re.I)})
                
                if not review_elements:
                    # If no reviews found, break
                    break
                
                for element in review_elements:
                    if len(reviews) >= max_reviews:
                        break
                    
                    # Extract review text
                    text_elem = element.find(['p', 'div'], class_=re.compile(r'text|content|review-text|body', re.I))
                    if not text_elem:
                        text_elem = element.find('p')
                    
                    review_text = text_elem.get_text(strip=True) if text_elem else ""
                    
                    if not review_text or len(review_text) < 20:  # Skip very short reviews
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
                            "source": "G2"
                        })
                
                # Check if there are more pages
                next_page = soup.find('a', {'aria-label': re.compile(r'next|page', re.I)})
                if not next_page or page >= 10:  # Limit to 10 pages
                    break
                
                page += 1
                
            except Exception as e:
                print(f"Error scraping G2 page {page} for {tool_name}: {str(e)}")
                break
        
        return reviews[:max_reviews]
