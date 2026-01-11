# Developer Guide

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment (recommended)

### Initial Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd B2B
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_scrapers.py

# Run with verbose output
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy . --ignore-missing-imports

# Security scan
bandit -r . -ll
```

## Project Structure

```
B2B/
├── analyzer/          # Pattern extraction and AI analysis
├── api/               # API endpoints
├── scraper/           # Web scrapers (sync and async)
├── utils/             # Utility modules (cache, db, logging, etc.)
├── tests/             # Test suite
├── docs/              # Documentation
├── app.py             # Main Streamlit app (legacy)
├── app_v2.py          # Enhanced Streamlit app
└── config.py          # Configuration
```

## Architecture

### Components

1. **Scrapers** (`scraper/`)
   - `BaseScraper`: Synchronous base scraper
   - `BaseAsyncScraper`: Async base scraper
   - `G2Scraper` / `G2ScraperAsync`: G2.com scraper
   - `CapterraScraper` / `CapterraScraperAsync`: Capterra scraper

2. **Analyzers** (`analyzer/`)
   - `PatternExtractor`: Basic pattern extraction (TF-IDF + K-Means)
   - `PatternExtractorV2`: Semantic pattern extraction (sentence transformers)
   - `XAIClient`: xAI Grok API client

3. **Utilities** (`utils/`)
   - `database.py`: Database management (SQLAlchemy)
   - `cache.py`: Caching utilities
   - `logging.py`: Structured logging
   - `security.py`: Security utilities
   - `monitoring.py`: Performance monitoring
   - `health.py`: Health checks
   - `retry.py`: Retry logic
   - `rate_limiter.py`: Rate limiting

### Data Flow

1. User selects tools → App
2. App → Scrapers (G2, Capterra)
3. Scrapers → Reviews (cached)
4. Reviews → Pattern Extractor
5. Patterns → xAI Client
6. AI Analysis → Product Ideas
7. Ideas → Roadmaps
8. Results → Database (persisted)

## Adding New Features

### Adding a New Scraper

1. Create new scraper class inheriting from `BaseScraper` or `BaseAsyncScraper`:
```python
from scraper.base_async import BaseAsyncScraper

class NewScraperAsync(BaseAsyncScraper):
    async def scrape_reviews(self, tool_name, ...):
        # Implementation
        pass
```

2. Add tests in `tests/test_scrapers.py`

3. Update `config.py` with new tool configuration

### Adding a New Analyzer

1. Create analyzer class:
```python
class NewAnalyzer:
    def analyze(self, data):
        # Implementation
        pass
```

2. Add tests in `tests/test_analyzer.py`

3. Integrate into `app_v2.py`

## Testing Guidelines

### Unit Tests

- Test individual functions/methods
- Mock external dependencies
- Test edge cases and error conditions

### Integration Tests

- Test component interactions
- Test full pipeline
- Use real dependencies where possible

### Test Structure

```python
class TestFeature:
    def test_basic_functionality(self):
        # Test basic case
        pass
    
    def test_edge_case(self):
        # Test edge case
        pass
    
    def test_error_handling(self):
        # Test error handling
        pass
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small and focused

### Formatting

- Use `black` for formatting (line length: 100)
- Use `ruff` for linting
- Use `mypy` for type checking

### Naming Conventions

- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

## Git Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Development branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Be descriptive and specific
- Reference issues when applicable

### Pull Requests

1. Create feature branch
2. Make changes and commit
3. Push to remote
4. Create pull request
5. Address review comments
6. Merge after approval

## CI/CD

### GitHub Actions

The CI pipeline runs on:
- Push to `main` or `develop`
- Pull requests

**Pipeline Steps:**
1. Lint code (black, ruff, mypy)
2. Run tests (pytest)
3. Security scan (bandit, safety)
4. Build Docker image

### Pre-commit Hooks

Automatically run on commit:
- Code formatting (black)
- Linting (ruff)
- Type checking (mypy)
- Security checks (bandit)

## Debugging

### Logging

Use structured logging:
```python
from utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Message", key=value)
logger.error("Error", error=str(e))
```

### Debug Mode

Set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

### Performance Monitoring

Use performance monitor:
```python
from utils.monitoring import monitor_performance

@monitor_performance("function_name")
def my_function():
    pass
```

## Deployment

### Docker

Build image:
```bash
docker build -t b2b-analyzer .
```

Run container:
```bash
docker run -p 8501:8501 -e XAI_API_KEY=your_key b2b-analyzer
```

### Docker Compose

```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Ensure all tests pass
6. Submit pull request

## Resources

- [Python Documentation](https://docs.python.org/3/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
