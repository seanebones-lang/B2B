"""Browser-based scraper using Playwright for anti-bot protection bypass"""

import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
from utils.logging import get_logger

logger = get_logger(__name__)


class PlaywrightScraper:
    """Scraper using Playwright for JavaScript-rendered pages"""
    
    def __init__(self):
        """Initialize Playwright scraper"""
        self.browser: Optional[Browser] = None
        logger.info("Playwright scraper initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def _create_page(self) -> Page:
        """Create a new page with stealth settings"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Add stealth scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return page
    
    async def scrape_g2_reviews(
        self,
        tool_name: str,
        tool_slug: Optional[str] = None,
        max_reviews: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Scrape G2 reviews using Playwright
        
        Args:
            tool_name: Name of the tool
            tool_slug: G2 slug (e.g., 'salesforce')
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            List of review dictionaries
        """
        if not tool_slug:
            tool_slug = tool_name.lower().replace(" ", "-")
        
        reviews = []
        page_num = 1
        
        try:
            page = await self._create_page()
            
            while len(reviews) < max_reviews:
                url = f"https://www.g2.com/products/{tool_slug}/reviews"
                params = f"?rating=1&rating=2&sort=newest&page={page_num}"
                full_url = url + params
                
                logger.info("Scraping G2 page", url=full_url, page=page_num)
                
                try:
                    # Navigate and wait for content
                    await page.goto(full_url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(2000)  # Additional wait for JS rendering
                    
                    # Get page content
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find review elements
                    review_elements = soup.find_all('div', class_='paper paper--white paper--box')
                    
                    if not review_elements:
                        logger.info("No more reviews found", page=page_num)
                        break
                    
                    for element in review_elements:
                        if len(reviews) >= max_reviews:
                            break
                        
                        # Extract review text
                        review_text_elem = element.find('div', itemprop='reviewBody')
                        if not review_text_elem:
                            continue
                        
                        review_text = review_text_elem.get_text(strip=True)
                        
                        # Extract rating
                        rating_elem = element.find('div', class_='stars')
                        rating = 1  # Default for filtered results
                        if rating_elem:
                            stars = rating_elem.find_all('div', class_='star')
                            rating = len([s for s in stars if 'full' in s.get('class', [])])
                        
                        # Extract date
                        date_elem = element.find('time')
                        date = date_elem.get('datetime', '') if date_elem else ''
                        
                        reviews.append({
                            'text': review_text,
                            'rating': rating,
                            'date': date,
                            'source': 'G2',
                            'tool': tool_name
                        })
                    
                    page_num += 1
                    await page.wait_for_timeout(3000)  # Polite delay
                    
                except Exception as e:
                    logger.error("Error scraping G2 page", error=str(e), page=page_num)
                    break
            
            await page.close()
            logger.info("G2 scraping complete", tool_name=tool_name, reviews_found=len(reviews))
            
        except Exception as e:
            logger.error("Error in G2 scraping", error=str(e), tool_name=tool_name)
        
        return reviews
    
    async def scrape_capterra_reviews(
        self,
        tool_name: str,
        tool_id: Optional[str] = None,
        max_reviews: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Scrape Capterra reviews using Playwright
        
        Args:
            tool_name: Name of the tool
            tool_id: Capterra product ID
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            List of review dictionaries
        """
        if not tool_id:
            logger.warning("No Capterra ID provided", tool_name=tool_name)
            return []
        
        reviews = []
        page_num = 1
        
        try:
            page = await self._create_page()
            
            while len(reviews) < max_reviews:
                url = f"https://www.capterra.com/p/{tool_id}/{tool_name.lower().replace(' ', '-')}/reviews/"
                params = f"?rating=1-2&sort=most_recent&page={page_num}"
                full_url = url + params
                
                logger.info("Scraping Capterra page", url=full_url, page=page_num)
                
                try:
                    await page.goto(full_url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(2000)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find review elements
                    review_elements = soup.find_all('div', class_='review-card')
                    
                    if not review_elements:
                        logger.info("No more reviews found", page=page_num)
                        break
                    
                    for element in review_elements:
                        if len(reviews) >= max_reviews:
                            break
                        
                        # Extract review text
                        review_text_elem = element.find('div', class_='review-text')
                        if not review_text_elem:
                            continue
                        
                        review_text = review_text_elem.get_text(strip=True)
                        
                        # Extract rating
                        rating_elem = element.find('div', class_='rating')
                        rating = 1  # Default
                        if rating_elem:
                            rating_text = rating_elem.get_text()
                            try:
                                rating = int(float(rating_text.split()[0]))
                            except:
                                pass
                        
                        # Extract date
                        date_elem = element.find('time')
                        date = date_elem.get('datetime', '') if date_elem else ''
                        
                        reviews.append({
                            'text': review_text,
                            'rating': rating,
                            'date': date,
                            'source': 'Capterra',
                            'tool': tool_name
                        })
                    
                    page_num += 1
                    await page.wait_for_timeout(3000)
                    
                except Exception as e:
                    logger.error("Error scraping Capterra page", error=str(e), page=page_num)
                    break
            
            await page.close()
            logger.info("Capterra scraping complete", tool_name=tool_name, reviews_found=len(reviews))
            
        except Exception as e:
            logger.error("Error in Capterra scraping", error=str(e), tool_name=tool_name)
        
        return reviews


async def scrape_with_playwright(
    tool_name: str,
    tool_slug: Optional[str] = None,
    tool_id: Optional[str] = None,
    max_reviews: int = 30
) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape both G2 and Capterra
    
    Args:
        tool_name: Name of the tool
        tool_slug: G2 slug
        tool_id: Capterra ID
        max_reviews: Max reviews per source
        
    Returns:
        Combined list of reviews
    """
    async with PlaywrightScraper() as scraper:
        reviews = []
        
        # Scrape G2
        if tool_slug:
            g2_reviews = await scraper.scrape_g2_reviews(tool_name, tool_slug, max_reviews)
            reviews.extend(g2_reviews)
        
        # Scrape Capterra
        if tool_id:
            capterra_reviews = await scraper.scrape_capterra_reviews(tool_name, tool_id, max_reviews)
            reviews.extend(capterra_reviews)
        
        return reviews
