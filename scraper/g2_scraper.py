"""G2.com review scraper"""

from bs4 import BeautifulSoup
from .base import BaseScraper
from utils.logging import get_logger
import re

logger = get_logger(__name__)


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
                    logger.debug("No review elements found", page=page, tool_name=tool_name)
                    break
                
                for element in review_elements:
                    if len(reviews) >= max_reviews:
                        break
                    
                    try:
                        # Extract review text with error handling
                        text_elem = element.find(['p', 'div'], class_=re.compile(r'text|content|review-text|body', re.I))
                        if not text_elem:
                            text_elem = element.find('p')
                        
                        review_text = text_elem.get_text(strip=True) if text_elem else ""
                        
                        if not review_text or len(review_text) < 20:  # Skip very short reviews
                            continue
                        
                        # Extract rating with error handling
                        rating_elem = element.find(['span', 'div'], class_=re.compile(r'rating|star', re.I))
                        rating = None
                        if rating_elem:
                            try:
                                rating_text = rating_elem.get_text(strip=True)
                                rating_match = re.search(r'(\d+)', rating_text)
                                if rating_match:
                                    rating = int(rating_match.group(1))
                            except (ValueError, AttributeError) as e:
                                logger.debug("Error extracting rating", error=str(e))
                                continue
                        
                        # Extract date with error handling
                        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time', re.I))
                        date = None
                        if date_elem:
                            try:
                                date = date_elem.get_text(strip=True)
                            except AttributeError:
                                pass
                        
                        # Only include 1-2 star reviews
                        if rating and rating <= 2:
                            reviews.append({
                                "text": review_text,
                                "rating": rating,
                                "date": date,
                                "source": "G2"
                            })
                    except Exception as e:
                        logger.warning("Error extracting review element", error=str(e), tool_name=tool_name)
                        continue  # Skip this element and continue
                
                # Check if there are more pages
                next_page = soup.find('a', {'aria-label': re.compile(r'next|page', re.I)})
                if not next_page or page >= 10:  # Limit to 10 pages
                    break
                
                page += 1
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                if status_code == 404:
                    logger.info("Page not found, stopping", page=page, tool_name=tool_name)
                    break
                elif status_code == 429:
                    logger.warning("Rate limited, stopping", page=page, tool_name=tool_name)
                    break
                else:
                    logger.error("HTTP error scraping G2 page", page=page, tool_name=tool_name, status_code=status_code, error=str(e))
                    break
            except requests.exceptions.Timeout as e:
                logger.error("Timeout scraping G2 page", page=page, tool_name=tool_name, error=str(e))
                break
            except requests.exceptions.RequestException as e:
                logger.error("Request error scraping G2 page", page=page, tool_name=tool_name, error=str(e))
                break
            except Exception as e:
                logger.error("Unexpected error scraping G2 page", page=page, tool_name=tool_name, error=str(e), error_type=type(e).__name__)
                break
        
        logger.info("Scraping complete", tool_name=tool_name, reviews_found=len(reviews), max_reviews=max_reviews)
        return reviews[:max_reviews]
