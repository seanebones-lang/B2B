"""Web research and fact-checking for complaints and ideas"""

from typing import List, Dict, Any, Optional
from utils.logging import get_logger
import requests
from bs4 import BeautifulSoup

logger = get_logger(__name__)


class WebResearcher:
    """Research and fact-check complaints and ideas using web search"""
    
    def __init__(self):
        """Initialize web researcher"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        logger.info("Web researcher initialized")
    
    def search_for_context(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search the web for context about a complaint or idea
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Use DuckDuckGo HTML search (no API key required)
            search_url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            
            response = requests.get(
                search_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning("Web search failed", status=response.status_code)
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse DuckDuckGo results (structure may vary)
            result_elements = soup.find_all('div', class_='result')
            
            # Fallback: try alternative selectors
            if not result_elements:
                result_elements = soup.find_all('div', {'class': lambda x: x and 'result' in x.lower()})
            
            for elem in result_elements[:max_results]:
                try:
                    # Try multiple selectors for title
                    title_elem = (
                        elem.find('a', class_='result__a') or
                        elem.find('a', class_='web-result') or
                        elem.find('h2') or
                        elem.find('a')
                    )
                    
                    # Try multiple selectors for snippet
                    snippet_elem = (
                        elem.find('a', class_='result__snippet') or
                        elem.find('div', class_='result__snippet') or
                        elem.find('p', class_='result__snippet') or
                        elem.find('span', class_='result__snippet')
                    )
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '') if title_elem.name == 'a' else ''
                        
                        # Extract link if not in title element
                        if not link:
                            link_elem = elem.find('a', href=True)
                            if link_elem:
                                link = link_elem.get('href', '')
                        
                        snippet = ''
                        if snippet_elem:
                            snippet = snippet_elem.get_text(strip=True)
                        else:
                            # Fallback: get any text content
                            text_elements = elem.find_all(['p', 'span', 'div'])
                            for te in text_elements:
                                text = te.get_text(strip=True)
                                if len(text) > 20 and text != title:
                                    snippet = text[:200]  # Limit snippet length
                                    break
                        
                        if title:  # Only add if we have a title
                            results.append({
                                'title': title,
                                'link': link,
                                'snippet': snippet,
                                'query': query
                            })
                except Exception as e:
                    logger.debug("Error parsing search result", error=str(e))
                    continue
            
            logger.info("Web search completed", query=query, results=len(results))
            return results
            
        except Exception as e:
            logger.error("Error in web search", error=str(e))
            return []
    
    def fact_check_complaint(
        self,
        complaint_text: str,
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Fact-check a complaint by searching for supporting evidence
        
        Args:
            complaint_text: Complaint text
            tool_name: Name of the tool
            
        Returns:
            Dictionary with fact-check results
        """
        # Extract key claims from complaint
        # Simple approach: search for tool name + common complaint keywords
        keywords = ['problem', 'issue', 'pricing', 'cost', 'missing', 'lack']
        found_keywords = [kw for kw in keywords if kw in complaint_text.lower()]
        
        if not found_keywords:
            return {
                'verified': False,
                'reason': 'No verifiable claims found',
                'sources': []
            }
        
        # Search for context
        query = f"{tool_name} {found_keywords[0]} 2025"
        search_results = self.search_for_context(query, max_results=3)
        
        # Simple verification: if we find similar complaints, it's likely valid
        verified = len(search_results) > 0
        
        return {
            'verified': verified,
            'reason': f"Found {len(search_results)} related sources" if verified else "No supporting sources found",
            'sources': search_results,
            'query': query
        }
    
    def validate_idea_novelty(
        self,
        idea_name: str,
        idea_description: str
    ) -> Dict[str, Any]:
        """
        Validate if an idea is novel by searching for similar products
        
        Args:
            idea_name: Name of the product idea
            idea_description: Description of the idea
            
        Returns:
            Dictionary with novelty validation results
        """
        # Search for similar products
        query = f'"{idea_name}" OR "{idea_description[:50]}" B2B SaaS 2025'
        search_results = self.search_for_context(query, max_results=5)
        
        # If we find many similar products, idea may not be novel
        novelty_score = max(0, 10 - len(search_results))  # 10 = novel, 0 = not novel
        
        return {
            'novelty_score': novelty_score,
            'similar_products_found': len(search_results),
            'sources': search_results,
            'recommendation': 'Novel idea' if novelty_score >= 7 else 'Consider differentiation' if novelty_score >= 4 else 'Market may be saturated'
        }
    
    def get_market_context(
        self,
        tool_name: str,
        complaint_type: str
    ) -> Dict[str, Any]:
        """
        Get market context for a complaint type
        
        Args:
            tool_name: Name of the tool
            complaint_type: Type of complaint (e.g., 'pricing', 'features')
            
        Returns:
            Dictionary with market context
        """
        # Search for market benchmarks
        query = f"{tool_name} {complaint_type} benchmarks market analysis 2025"
        search_results = self.search_for_context(query, max_results=5)
        
        return {
            'context_found': len(search_results) > 0,
            'sources': search_results,
            'query': query
        }
