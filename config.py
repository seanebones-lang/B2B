"""
Configuration file for B2B Complaint Analyzer
Contains tool list, keywords, and settings
"""

# Top 10 B2B SaaS tools to analyze
B2B_TOOLS = [
    {"name": "Salesforce", "category": "CRM", "g2_slug": "salesforce", "capterra_id": "165"},
    {"name": "HubSpot", "category": "CRM/Marketing", "g2_slug": "hubspot", "capterra_id": "1007"},
    {"name": "Slack", "category": "Comms", "g2_slug": "slack", "capterra_id": "175"},
    {"name": "Asana", "category": "PM", "g2_slug": "asana", "capterra_id": "110"},
    {"name": "Notion", "category": "Productivity", "g2_slug": "notion", "capterra_id": "179"},
    {"name": "Zoom", "category": "Video", "g2_slug": "zoom", "capterra_id": "115"},
    {"name": "Intercom", "category": "Customer Support", "g2_slug": "intercom", "capterra_id": "1005"},
    {"name": "Zendesk", "category": "Customer Support", "g2_slug": "zendesk", "capterra_id": "103"},
    {"name": "Workday", "category": "HRIS", "g2_slug": "workday", "capterra_id": "1008"},
    {"name": "BambooHR", "category": "HRIS", "g2_slug": "bamboo-hr", "capterra_id": "1009"},
]

# Pain point keywords/phrases for pattern extraction
PAIN_KEYWORDS = {
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

# Pattern detection thresholds
MIN_PATTERN_MENTIONS = 5  # Minimum mentions to consider a pattern
PATTERN_FREQUENCY_THRESHOLD = 0.15  # 15% of reviews

# Scraping settings
MAX_REVIEWS_PER_TOOL = 30
SCRAPE_DELAY_MIN = 2  # seconds
SCRAPE_DELAY_MAX = 5  # seconds
REQUEST_TIMEOUT = 30  # seconds

# xAI Grok settings
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-beta"
