"""GitHub Issues scraper for product complaints and feature requests"""

import re
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)


class GitHubScraper:
    """Scraper for GitHub issues (complaints, bugs, feature requests)"""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub scraper
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'B2B-Complaint-Analyzer'
        }
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
        
        logger.info("GitHub scraper initialized")
    
    def scrape_issues(
        self,
        tool_name: str,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        max_issues: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape GitHub issues for complaints and feature requests
        
        Args:
            tool_name: Name of the tool
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            max_issues: Maximum number of issues to collect
            
        Returns:
            List of issue dictionaries
        """
        if not repo_owner or not repo_name:
            logger.warning("No GitHub repo specified", tool_name=tool_name)
            return []
        
        issues = []
        page = 1
        per_page = 30
        
        try:
            while len(issues) < max_issues:
                url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues"
                params = {
                    'state': 'all',  # Both open and closed
                    'sort': 'created',
                    'direction': 'desc',
                    'per_page': per_page,
                    'page': page,
                    'labels': 'bug,enhancement,feature-request'  # Focus on complaints/requests
                }
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                
                if response.status_code != 200:
                    logger.warning("GitHub API request failed", status=response.status_code)
                    break
                
                data = response.json()
                
                if not data:
                    break
                
                for issue in data:
                    if len(issues) >= max_issues:
                        break
                    
                    # Skip pull requests
                    if 'pull_request' in issue:
                        continue
                    
                    title = issue.get('title', '')
                    body = issue.get('body', '') or ''
                    state = issue.get('state', '')
                    labels = [label.get('name', '') for label in issue.get('labels', [])]
                    created_at = issue.get('created_at', '')
                    comments_count = issue.get('comments', 0)
                    
                    # Combine title and body
                    full_text = f"{title}\n\n{body}".strip()
                    
                    # Filter short issues
                    if len(full_text) < 30:
                        continue
                    
                    # Determine severity/rating based on labels and content
                    is_bug = 'bug' in labels or 'bug' in full_text.lower()
                    is_critical = any(word in full_text.lower() for word in ['critical', 'urgent', 'blocker', 'broken'])
                    
                    rating = 1 if (is_bug and is_critical) else 2
                    
                    issues.append({
                        'text': full_text,
                        'rating': rating,
                        'date': created_at,
                        'source': f'GitHub ({repo_owner}/{repo_name})',
                        'tool': tool_name,
                        'metadata': {
                            'state': state,
                            'labels': labels,
                            'comments': comments_count,
                            'url': issue.get('html_url', '')
                        }
                    })
                
                page += 1
                
                # Rate limiting
                import time
                time.sleep(1)
            
            logger.info("GitHub scraping complete", 
                       tool_name=tool_name, 
                       issues_found=len(issues))
            
        except Exception as e:
            logger.error("Error scraping GitHub", error=str(e), tool_name=tool_name)
        
        return issues
