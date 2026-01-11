"""
Configuration file for B2B Complaint Analyzer
Contains tool list, keywords, and settings with environment variable support
"""

import os
from typing import List, Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Scraping settings
    scrape_delay_min: int = int(os.getenv("SCRAPE_DELAY_MIN", "2"))
    scrape_delay_max: int = int(os.getenv("SCRAPE_DELAY_MAX", "5"))
    scrape_timeout: int = int(os.getenv("SCRAPE_TIMEOUT", "30"))
    max_reviews_per_tool: int = int(os.getenv("MAX_REVIEWS_PER_TOOL", "30"))
    
    # Pattern detection thresholds
    min_pattern_mentions: int = int(os.getenv("MIN_PATTERN_MENTIONS", "5"))
    pattern_frequency_threshold: float = float(os.getenv("PATTERN_FREQUENCY_THRESHOLD", "0.15"))
    
    # xAI Grok settings (Updated Jan 2026 - Grok 4.1 Fast with 2M token context)
    xai_base_url: str = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
    xai_model: str = os.getenv("XAI_MODEL", "grok-3")  # Fallback: grok-3 (stable), Latest: grok-4.1-fast-reasoning
    xai_temperature: float = float(os.getenv("XAI_TEMPERATURE", "0.3"))
    xai_max_tokens: int = int(os.getenv("XAI_MAX_TOKENS", "2000"))
    
    # Compliance settings
    gdpr_enabled: bool = os.getenv("GDPR_ENABLED", "true").lower() == "true"
    data_retention_days: int = int(os.getenv("DATA_RETENTION_DAYS", "90"))
    enable_audit_logging: bool = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings
settings = Settings()

# Top 10 B2B SaaS tools to analyze (with multi-source metadata)
B2B_TOOLS: List[Dict[str, str]] = [
    {"name": "Salesforce", "category": "CRM", "g2_slug": "salesforce", "capterra_id": "165", "ph_slug": "salesforce", "trustpilot_slug": "www.salesforce.com"},
    {"name": "HubSpot", "category": "CRM/Marketing", "g2_slug": "hubspot", "capterra_id": "1007", "ph_slug": "hubspot", "trustpilot_slug": "www.hubspot.com"},
    {"name": "Slack", "category": "Comms", "g2_slug": "slack", "capterra_id": "175", "ph_slug": "slack", "trustpilot_slug": "slack.com"},
    {"name": "Asana", "category": "PM", "g2_slug": "asana", "capterra_id": "110", "ph_slug": "asana", "trustpilot_slug": "asana.com"},
    {"name": "Notion", "category": "Productivity", "g2_slug": "notion", "capterra_id": "179", "ph_slug": "notion-2-0", "trustpilot_slug": "notion.so"},
    {"name": "Zoom", "category": "Video", "g2_slug": "zoom", "capterra_id": "115", "ph_slug": "zoom", "trustpilot_slug": "zoom.us"},
    {"name": "Intercom", "category": "Customer Support", "g2_slug": "intercom", "capterra_id": "1005", "ph_slug": "intercom", "trustpilot_slug": "www.intercom.com"},
    {"name": "Zendesk", "category": "Customer Support", "g2_slug": "zendesk", "capterra_id": "103", "ph_slug": "zendesk", "trustpilot_slug": "www.zendesk.com"},
    {"name": "Workday", "category": "HRIS", "g2_slug": "workday", "capterra_id": "1008", "ph_slug": "workday", "trustpilot_slug": "www.workday.com"},
    {"name": "BambooHR", "category": "HRIS", "g2_slug": "bamboo-hr", "capterra_id": "1009", "ph_slug": "bamboohr", "trustpilot_slug": "www.bamboohr.com"},
]

# Pain point keywords/phrases for pattern extraction
PAIN_KEYWORDS: Dict[str, List[str]] = {
    "missing_feature": [
        "doesn't have", "doesn't have", "missing", "lacks", "no way to", 
        "absent", "without", "does not have", "does not support"
    ],
    "wish_desire": [
        "wish it could", "if only", "should have", "need to", 
        "want to be able to", "would like", "hoping for", "expect"
    ],
    "cant_blocks": [
        "can't", "cannot", "unable to", "blocks me from", "prevents", 
        "frustrated by lack of", "impossible to", "won't let me"
    ]
}

# Backward compatibility exports
MAX_REVIEWS_PER_TOOL = settings.max_reviews_per_tool
SCRAPE_DELAY_MIN = settings.scrape_delay_min
SCRAPE_DELAY_MAX = settings.scrape_delay_max
REQUEST_TIMEOUT = settings.scrape_timeout
MIN_PATTERN_MENTIONS = settings.min_pattern_mentions
PATTERN_FREQUENCY_THRESHOLD = settings.pattern_frequency_threshold
XAI_BASE_URL = settings.xai_base_url
XAI_MODEL = settings.xai_model
