"""Multi-source scraper that combines all data sources with fallbacks and async improvements"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from utils.logging import get_logger

logger = get_logger(__name__)


class MultiSourceScraper:
    """Scraper that combines multiple data sources with intelligent fallbacks"""
    
    def __init__(self):
        """Initialize multi-source scraper"""
        self.sources = []
        logger.info("Multi-source scraper initialized")
    
    def scrape_all_sources(
        self,
        tool_name: str,
        tool_slug: Optional[str] = None,
        tool_id: Optional[str] = None,
        product_slug: Optional[str] = None,
        max_per_source: int = 30,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Scrape from all available sources with fallbacks
        
        Args:
            tool_name: Name of the tool
            tool_slug: G2 slug
            tool_id: Capterra ID
            product_slug: Product Hunt slug
            max_per_source: Max reviews per source
            
        Returns:
            Combined list of reviews/complaints
        """
        all_reviews = []
        sources_tried = []
        sources_succeeded = []
        
        # 1. Try Playwright-based scraping (G2 + Capterra)
        try:
            logger.info("Attempting Playwright scraping", tool_name=tool_name)
            sources_tried.append("Playwright (G2/Capterra)")
            
            from scraper.playwright_scraper import scrape_with_playwright
            
            playwright_reviews = asyncio.run(
                scrape_with_playwright(tool_name, tool_slug, tool_id, max_per_source)
            )
            
            if playwright_reviews:
                all_reviews.extend(playwright_reviews)
                sources_succeeded.append(f"Playwright ({len(playwright_reviews)} reviews)")
                logger.info("Playwright scraping successful", count=len(playwright_reviews))
        except Exception as e:
            logger.warning("Playwright scraping failed", error=str(e))
        
        # 2. Try Reddit scraping
        try:
            logger.info("Attempting Reddit scraping", tool_name=tool_name)
            sources_tried.append("Reddit")
            
            from scraper.reddit_scraper import RedditScraper
            
            reddit_scraper = RedditScraper()
            reddit_complaints = reddit_scraper.scrape_product_complaints(
                tool_name,
                max_posts=max_per_source,
                date_from=date_from,
                date_to=date_to
            )
            
            if reddit_complaints:
                all_reviews.extend(reddit_complaints)
                sources_succeeded.append(f"Reddit ({len(reddit_complaints)} posts)")
                logger.info("Reddit scraping successful", count=len(reddit_complaints))
        except Exception as e:
            logger.warning("Reddit scraping failed", error=str(e))
        
        # 3. Try Twitter scraping
        try:
            logger.info("Attempting Twitter scraping", tool_name=tool_name)
            sources_tried.append("Twitter")
            
            from scraper.twitter_scraper import TwitterScraper
            
            twitter_scraper = TwitterScraper()
            twitter_mentions = twitter_scraper.scrape_product_mentions(
                tool_name,
                max_tweets=max_per_source
            )
            
            if twitter_mentions:
                all_reviews.extend(twitter_mentions)
                sources_succeeded.append(f"Twitter ({len(twitter_mentions)} tweets)")
                logger.info("Twitter scraping successful", count=len(twitter_mentions))
        except Exception as e:
            logger.warning("Twitter scraping failed", error=str(e))
        
        # 4. Try Product Hunt scraping
        if product_slug:
            try:
                logger.info("Attempting Product Hunt scraping", tool_name=tool_name)
                sources_tried.append("Product Hunt")
                
                from scraper.producthunt_scraper import ProductHuntScraper
                
                ph_scraper = ProductHuntScraper()
                ph_comments = ph_scraper.scrape_product_comments(
                    tool_name,
                    product_slug=product_slug,
                    max_comments=max_per_source
                )
                
                if ph_comments:
                    all_reviews.extend(ph_comments)
                    sources_succeeded.append(f"Product Hunt ({len(ph_comments)} comments)")
                    logger.info("Product Hunt scraping successful", count=len(ph_comments))
            except Exception as e:
                logger.warning("Product Hunt scraping failed", error=str(e))
        
        # 5. Try GitHub Issues
        try:
            logger.info("Attempting GitHub scraping", tool_name=tool_name)
            sources_tried.append("GitHub")
            
            from scraper.github_scraper import GitHubScraper
            
            github_scraper = GitHubScraper()
            # You can add repo_owner and repo_name to config for each tool
            # For now, skip if not configured
            # github_issues = github_scraper.scrape_issues(tool_name, repo_owner, repo_name, max_per_source)
            
        except Exception as e:
            logger.warning("GitHub scraping failed", error=str(e))
        
        # Use asyncio.gather for parallel scraping (Phase 2 improvement)
        # Note: Some scrapers are async, some are sync - this is a hybrid approach
        # For full async, convert all scrapers to async
        
        # 6. Try Trustpilot
        try:
            logger.info("Attempting Trustpilot scraping", tool_name=tool_name)
            sources_tried.append("Trustpilot")
            
            from scraper.trustpilot_scraper import TrustpilotScraper
            
            trustpilot_scraper = TrustpilotScraper()
            trustpilot_reviews = trustpilot_scraper.scrape_reviews(
                tool_name,
                max_reviews=max_per_source
            )
            
            if trustpilot_reviews:
                all_reviews.extend(trustpilot_reviews)
                sources_succeeded.append(f"Trustpilot ({len(trustpilot_reviews)} reviews)")
                logger.info("Trustpilot scraping successful", count=len(trustpilot_reviews))
        except Exception as e:
            logger.warning("Trustpilot scraping failed", error=str(e))
        
        # 7. Try Hacker News
        try:
            logger.info("Attempting Hacker News scraping", tool_name=tool_name)
            sources_tried.append("Hacker News")
            
            from scraper.hackernews_scraper import HackerNewsScraper
            
            hn_scraper = HackerNewsScraper()
            hn_discussions = hn_scraper.scrape_discussions(
                tool_name,
                max_items=max_per_source
            )
            
            if hn_discussions:
                all_reviews.extend(hn_discussions)
                sources_succeeded.append(f"Hacker News ({len(hn_discussions)} discussions)")
                logger.info("Hacker News scraping successful", count=len(hn_discussions))
        except Exception as e:
            logger.warning("Hacker News scraping failed", error=str(e))
        
        # 8. Try LinkedIn (Phase 2)
        try:
            logger.info("Attempting LinkedIn scraping", tool_name=tool_name)
            sources_tried.append("LinkedIn")
            
            from scraper.linkedin_scraper import LinkedInScraper
            
            linkedin_scraper = LinkedInScraper()
            linkedin_complaints = linkedin_scraper.scrape_b2b_complaints(
                tool_name,
                max_posts=max_per_source,
                date_from=date_from,
                date_to=date_to
            )
            
            if linkedin_complaints:
                all_reviews.extend(linkedin_complaints)
                sources_succeeded.append(f"LinkedIn ({len(linkedin_complaints)} posts)")
                logger.info("LinkedIn scraping successful", count=len(linkedin_complaints))
        except Exception as e:
            logger.warning("LinkedIn scraping failed", error=str(e))
        
        # 9. Try Google News (Phase 2)
        try:
            logger.info("Attempting Google News scraping", tool_name=tool_name)
            sources_tried.append("Google News")
            
            from scraper.google_news_scraper import GoogleNewsScraper
            
            news_scraper = GoogleNewsScraper()
            news_articles = news_scraper.scrape_product_news(
                tool_name,
                max_articles=max_per_source,
                date_from=date_from,
                date_to=date_to
            )
            
            if news_articles:
                all_reviews.extend(news_articles)
                sources_succeeded.append(f"Google News ({len(news_articles)} articles)")
                logger.info("Google News scraping successful", count=len(news_articles))
        except Exception as e:
            logger.warning("Google News scraping failed", error=str(e))
        
        # 10. Fallback to original scrapers (requests-based)
        if len(all_reviews) < 10:  # If we don't have enough data
            try:
                logger.info("Attempting fallback to original scrapers", tool_name=tool_name)
                sources_tried.append("Original Scrapers")
                
                from scraper import G2Scraper, CapterraScraper
                
                g2_scraper = G2Scraper()
                capterra_scraper = CapterraScraper()
                
                try:
                    g2_reviews = g2_scraper.scrape_reviews(tool_name, tool_slug, max_reviews=max_per_source)
                    if g2_reviews:
                        all_reviews.extend(g2_reviews)
                        sources_succeeded.append(f"G2 ({len(g2_reviews)} reviews)")
                except:
                    pass
                
                try:
                    capterra_reviews = capterra_scraper.scrape_reviews(tool_name, tool_id, max_reviews=max_per_source)
                    if capterra_reviews:
                        all_reviews.extend(capterra_reviews)
                        sources_succeeded.append(f"Capterra ({len(capterra_reviews)} reviews)")
                except:
                    pass
                
            except Exception as e:
                logger.warning("Original scrapers failed", error=str(e))
        
        logger.info(
            "Multi-source scraping complete",
            tool_name=tool_name,
            total_reviews=len(all_reviews),
            sources_tried=sources_tried,
            sources_succeeded=sources_succeeded
        )
        
        return all_reviews, sources_succeeded
