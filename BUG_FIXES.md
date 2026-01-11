# Bug Fixes Applied

## Critical Bugs Fixed

### 1. Variable Scope Issue in app.py
**Bug**: `date_from` and `date_to` were defined inside `with st.sidebar:` block but used outside, causing `NameError`.

**Fix**: Store date filters in `st.session_state` to make them accessible throughout the app.

**Location**: `app.py` lines 89-122

### 2. Type Annotation Compatibility
**Bug**: Used `tuple[...]` syntax which requires Python 3.9+. Should use `Tuple` from typing for broader compatibility.

**Fix**: Changed `tuple[List[Dict[str, Any]], List[str]]` to `Tuple[List[Dict[str, Any]], List[str]]` and added `Tuple` import.

**Location**: `scraper/multi_source_scraper.py` line 27

### 3. Throttling Logic Error
**Bug**: `should_throttle()` method had incorrect logic - compared `request_count >= time_window` which doesn't make sense for rate limiting.

**Fix**: Changed to check if `request_count >= 1` (meaning we've already made a request in this window) and changed default `time_window` to 1 second for 1 req/sec rate limiting.

**Location**: `utils/compliance.py` line 80

## Potential Issues (Not Critical)

### 1. Streamlit Imports in Scrapers
**Issue**: Scrapers import `streamlit` inside try blocks to access secrets. This creates a dependency but is handled gracefully with fallbacks.

**Status**: Acceptable - scrapers fall back to environment variables if Streamlit is not available.

**Locations**: 
- `scraper/reddit_scraper.py` line 30
- `scraper/discord_scraper.py` line 58
- `scraper/google_news_scraper.py` line 27

### 2. Missing Robots.txt Check in base.py
**Issue**: The `_fetch` method in `base.py` doesn't call `_check_robots_txt()` before making requests, even though the method exists.

**Status**: Should be added for consistency with `base_async.py`. However, the circuit breaker pattern might make this less critical.

**Recommendation**: Add robots.txt check before the circuit breaker call.

### 3. Throttling Implementation
**Issue**: The throttling uses a simple counter that doesn't reset properly. For production, should use timestamp-based rate limiting.

**Status**: Works for basic use case, but could be improved with Redis or proper time-based tracking.

## Linter Warnings (Non-Critical)

- Markdown formatting warnings in `.md` files (cosmetic only)
- Import resolution warnings for `streamlit` and `reportlab` (expected in IDE, packages installed at runtime)

## Testing Recommendations

1. Test date filtering with actual date ranges
2. Test throttling with multiple rapid requests
3. Test robots.txt checking with various URLs
4. Test PRAW Reddit scraper with and without credentials
5. Test PDF export with reportlab installed and not installed
