# API Reference

## Overview

This document provides API reference for the B2B Complaint Analyzer modules.

## Scrapers

### BaseScraper

Base class for synchronous scrapers.

```python
from scraper.base import BaseScraper

class MyScraper(BaseScraper):
    def scrape_reviews(self, tool_name, tool_slug=None, tool_id=None, max_reviews=30):
        # Implementation
        pass
```

**Methods:**
- `_fetch(url, max_retries=3)`: Fetch URL with retries
- `_get_headers()`: Generate random headers
- `_delay()`: Random delay between requests

### BaseAsyncScraper

Base class for asynchronous scrapers.

```python
from scraper.base_async import BaseAsyncScraper

class MyScraperAsync(BaseAsyncScraper):
    async def scrape_reviews(self, tool_name, tool_slug=None, tool_id=None, max_reviews=30):
        # Implementation
        pass
```

**Methods:**
- `async _fetch(url, max_retries=3)`: Async fetch URL with retries
- `_get_headers()`: Generate random headers
- `async _delay()`: Async random delay

### G2Scraper

Synchronous G2.com scraper.

```python
from scraper import G2Scraper

scraper = G2Scraper()
reviews = scraper.scrape_reviews("Salesforce", tool_slug="salesforce", max_reviews=30)
```

### CapterraScraper

Synchronous Capterra scraper.

```python
from scraper import CapterraScraper

scraper = CapterraScraper()
reviews = scraper.scrape_reviews("Salesforce", tool_id="165", max_reviews=30)
```

## Analyzers

### PatternExtractor

Basic pattern extraction using TF-IDF + K-Means.

```python
from analyzer import PatternExtractor

extractor = PatternExtractor()
results = extractor.extract_patterns(reviews)
```

**Returns:**
```python
{
    "patterns": [
        {
            "description": "Missing feature X",
            "frequency": 10,
            "reviews": [...]
        }
    ],
    "total_reviews": 30,
    "categorized_complaints": {...}
}
```

### PatternExtractorV2

Semantic pattern extraction using sentence transformers.

```python
from analyzer import PatternExtractorV2

extractor = PatternExtractorV2(use_semantic=True)
results = extractor.extract_patterns(reviews)
```

**Parameters:**
- `use_semantic` (bool): Use semantic analysis (default: True)
- `model_name` (str): Sentence transformer model (default: "all-MiniLM-L6-v2")

### XAIClient

xAI Grok API client.

```python
from analyzer import XAIClient

client = XAIClient(api_key="your-api-key")

# Analyze patterns
analysis = client.analyze_patterns(tool_name, patterns, reviews)

# Generate product ideas
ideas = client.generate_product_ideas(tool_name, top_patterns)

# Generate roadmap
roadmap = client.generate_roadmap(product_idea)
```

**Methods:**
- `analyze_patterns(tool_name, patterns, reviews)`: Analyze complaint patterns
- `generate_product_ideas(tool_name, top_patterns)`: Generate product ideas
- `generate_roadmap(product_idea)`: Generate 4-week roadmap

## Utilities

### DatabaseManager

Database operations manager.

```python
from utils.database import get_db_manager

db = get_db_manager()

# Save reviews
count = db.save_reviews("Tool Name", reviews)

# Get reviews
reviews = db.get_reviews("Tool Name", limit=100)

# Save analysis result
result_id = db.save_analysis_result(
    tool_name="Tool Name",
    session_id="session-123",
    patterns={...},
    ai_analysis={...},
    product_ideas=[...]
)

# Get analysis result
result = db.get_analysis_result(result_id)

# Cleanup expired data
deleted = db.cleanup_expired_data()

# Delete user data
deleted = db.delete_user_data(session_id)
```

### CacheManager

Caching utilities.

```python
from utils.cache import CacheManager

cache = CacheManager()

# Set cache
cache.set("key", data, ttl=3600)

# Get cache
data = cache.get("key")

# Clear cache
cache.clear()
```

### PerformanceMonitor

Performance monitoring.

```python
from utils.monitoring import get_monitor, monitor_performance

monitor = get_monitor()

# Record metric
monitor.record_metric("scraping_duration", 1.5)

# Increment counter
monitor.increment_counter("requests", 1)

# Start/stop timer
timer_id = monitor.start_timer("operation")
# ... do work ...
duration = monitor.stop_timer(timer_id)

# Get stats
stats = monitor.get_stats()

# Decorator
@monitor_performance("function_name")
def my_function():
    pass
```

### HealthChecker

Health check utilities.

```python
from utils.health import get_health_checker

checker = get_health_checker()

# Check health
health = checker.check_health()

# Get metrics
metrics = checker.get_metrics()
```

### SecurityManager

Security utilities.

```python
from utils.security import SecurityManager, InputValidator

security = SecurityManager()

# Get API key
api_key = security.get_api_key("streamlit")

# Sanitize input
sanitized = InputValidator.sanitize_string(user_input)

# Validate API key
is_valid = InputValidator.validate_api_key(api_key)

# Detect XSS
has_xss = InputValidator.detect_xss(user_input)

# Detect SQL injection
has_sql_injection = InputValidator.detect_sql_injection(user_input)
```

## Configuration

### Settings

Access configuration via `config.settings`:

```python
import config

# Scraping settings
delay_min = config.settings.scrape_delay_min
delay_max = config.settings.scrape_delay_max
timeout = config.settings.scrape_timeout

# Pattern detection
min_mentions = config.settings.min_pattern_mentions
frequency_threshold = config.settings.pattern_frequency_threshold

# xAI settings
base_url = config.settings.xai_base_url
model = config.settings.xai_model
temperature = config.settings.xai_temperature
max_tokens = config.settings.xai_max_tokens
```

### Tools Configuration

```python
import config

# Get all tools
tools = config.B2B_TOOLS

# Get pain keywords
keywords = config.PAIN_KEYWORDS
```

## Error Handling

All modules use structured logging for errors:

```python
from utils.logging import get_logger

logger = get_logger(__name__)

try:
    # Operation
    pass
except Exception as e:
    logger.error("Operation failed", error=str(e), exc_info=True)
```

## Retry Logic

Use retry decorators:

```python
from utils.retry import retry_scraper, retry_api_call

@retry_scraper(max_attempts=3)
def scrape():
    pass

@retry_api_call(max_attempts=3)
def api_call():
    pass
```

## Rate Limiting

```python
from utils.rate_limiter import RateLimiter

limiter = RateLimiter()

if limiter.is_allowed("user-id"):
    # Process request
    pass
```
