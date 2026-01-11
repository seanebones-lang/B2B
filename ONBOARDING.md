# Onboarding Guide

Welcome to the **B2B Complaint-Driven Product Ideation App**! This guide will help you get started, whether you're a user looking to discover product opportunities or a developer contributing to the project.

## 🎯 What Is This Project?

This application automates complaint-driven product discovery by:

1. **Scraping Negative Reviews**: Automatically collects 1-2 star reviews from G2.com and Capterra for popular B2B SaaS tools
2. **Identifying Pain Patterns**: Uses keyword matching and machine learning clustering to find recurring complaint themes
3. **AI-Powered Analysis**: Leverages xAI's Grok to analyze patterns, assess impact, and generate novel product ideas
4. **Actionable Roadmaps**: Creates detailed 4-week solo founder roadmaps for the top opportunities

**The Core Philosophy**: Every complaint is a "pre-paid invoice" from future customers. This system helps entrepreneurs identify validated market needs and build products that solve real problems.

## 🚀 Quick Start (5 Minutes)

### For Users

1. **Install Python 3.10+** (if not already installed)
   ```bash
   python --version  # Should show 3.10 or higher
   ```

2. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd B2B
   pip install -r requirements.txt
   ```

3. **Get an xAI API Key**
   - Visit [x.ai/api](https://x.ai/api)
   - Sign up and get your API key

4. **Run the App**
   ```bash
   streamlit run app_v2.py
   ```
   The app will open at `http://localhost:8501`

5. **First Analysis**
   - Enter your xAI API key in the sidebar
   - Select 1-2 tools (e.g., "Salesforce" and "HubSpot")
   - Choose "Semantic Analysis" (recommended)
   - Click "Run Analysis"
   - Explore the results!

### For Developers

1. **Complete the User Setup** (above)

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your XAI_API_KEY
   ```

3. **Run Tests**
   ```bash
   pytest tests/
   ```

4. **Explore the Codebase**
   - Start with `app_v2.py` (main application)
   - Check `config.py` (configuration)
   - Review `scraper/` (web scraping logic)
   - Examine `analyzer/` (pattern extraction and AI)

## 📚 Understanding the System

### Architecture Overview

```
┌─────────────┐
│   User      │
│  (Streamlit)│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Tool Selection │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐     ┌──────────────┐
│  G2 Scraper     │     │ Capterra     │
│                 │     │ Scraper      │
└──────┬──────────┘     └──────┬───────┘
       │                       │
       └───────────┬───────────┘
                   ▼
            ┌──────────────┐
            │   Reviews    │
            │   (Cached)   │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │   Pattern    │
            │   Extractor  │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  xAI Grok    │
            │   Analysis   │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ Product Ideas│
            │  & Roadmaps  │
            └──────────────┘
```

### Key Components

#### 1. **Scrapers** (`scraper/`)
- **G2Scraper**: Scrapes reviews from G2.com
- **CapterraScraper**: Scrapes reviews from Capterra
- **Base Scrapers**: Provide anti-detection, retry logic, and error handling

#### 2. **Analyzers** (`analyzer/`)
- **PatternExtractor**: Basic pattern detection (TF-IDF + K-Means)
- **PatternExtractorV2**: Advanced semantic analysis (sentence transformers)
- **XAIClient**: Interfaces with xAI Grok API

#### 3. **Utilities** (`utils/`)
- **Cache**: Review caching to avoid re-scraping
- **Database**: SQLAlchemy for data persistence
- **Logging**: Structured logging with structlog
- **Security**: API key management and GDPR compliance

#### 4. **Application** (`app_v2.py`)
- Streamlit-based web interface
- Handles user interactions and displays results

## 🎓 Key Concepts

### Complaint Patterns

The system identifies three types of pain points:

1. **Missing Features**: Things the tool doesn't have
   - Keywords: "doesn't have", "missing", "lacks", "no way to"

2. **Wishes/Desires**: Things users want
   - Keywords: "wish it could", "if only", "should have", "would like"

3. **Blockers**: Things that prevent users from doing something
   - Keywords: "can't", "cannot", "unable to", "blocks me from"

### Pattern Detection Methods

**Standard Analysis** (TF-IDF + K-Means):
- Faster processing
- Good for keyword-based patterns
- Less accurate for semantic similarity

**Semantic Analysis** (Sentence Transformers):
- More accurate pattern detection
- Understands context and meaning
- Slower processing
- Recommended for best results

### Product Ideas

Each generated idea includes:
- **Name**: Catchy product name
- **Value Proposition**: One-sentence pitch
- **Target Audience**: Who would use this
- **MVP Scope**: Core features for minimum viable product
- **Monetization**: Pricing strategy

### Roadmaps

4-week solo founder roadmaps break down as:
- **Week 1**: Validation (surveys, interviews, market research)
- **Week 2**: MVP Development (landing page, core features)
- **Week 3**: Launch (marketing, initial users, feedback)
- **Week 4**: Iteration (improvements, scaling, next steps)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# xAI API Configuration
XAI_API_KEY=your-api-key-here
XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=grok-beta
XAI_TEMPERATURE=0.3
XAI_MAX_TOKENS=2000

# Scraping Configuration
SCRAPE_DELAY_MIN=2
SCRAPE_DELAY_MAX=5
SCRAPE_TIMEOUT=30
MAX_REVIEWS_PER_TOOL=30

# Pattern Detection
MIN_PATTERN_MENTIONS=5
PATTERN_FREQUENCY_THRESHOLD=0.15

# Compliance
GDPR_ENABLED=true
DATA_RETENTION_DAYS=90
ENABLE_AUDIT_LOGGING=true
```

### Adding New Tools

Edit `config.py` to add new B2B SaaS tools:

```python
B2B_TOOLS: List[Dict[str, str]] = [
    {
        "name": "YourTool",
        "category": "Category",
        "g2_slug": "your-tool-slug",
        "capterra_id": "capterra-id"
    },
    # ... existing tools
]
```

## 📖 Common Workflows

### Workflow 1: Quick Product Discovery

**Goal**: Find 3 product ideas in 10 minutes

1. Select 2 popular tools (e.g., Salesforce + HubSpot)
2. Use Semantic Analysis
3. Review "Top 3 Opportunities" tab
4. Export results as Markdown

**Expected Time**: 5-10 minutes

### Workflow 2: Deep Market Research

**Goal**: Comprehensive analysis of a specific category

1. Select 3 tools from the same category (e.g., all CRM tools)
2. Use Semantic Analysis
3. Review all tabs: Summary, Per-Tool Breakdown, Top 3 Opportunities
4. Export as JSON for further analysis
5. Compare patterns across tools

**Expected Time**: 15-30 minutes

### Workflow 3: Competitive Analysis

**Goal**: Understand pain points in competitor tools

1. Select competitor tools
2. Run analysis
3. Focus on "Per-Tool Breakdown" tab
4. Identify unique pain points
5. Use insights for product positioning

**Expected Time**: 10-20 minutes

## 🛠️ Development Workflow

### Making Your First Contribution

1. **Fork the Repository**
   ```bash
   git clone <your-fork-url>
   cd B2B
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write code following the style guide (see Developer Guide)
   - Add tests for new functionality
   - Update documentation if needed

4. **Test Your Changes**
   ```bash
   # Format code
   black .
   
   # Lint
   ruff check .
   
   # Type check
   mypy . --ignore-missing-imports
   
   # Run tests
   pytest tests/
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to GitHub
   - Create pull request
   - Fill out the PR template
   - Wait for review

### Code Style

- **Formatting**: Use `black` (line length: 100)
- **Linting**: Use `ruff`
- **Type Checking**: Use `mypy`
- **Naming**: 
  - Classes: `PascalCase`
  - Functions: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_scrapers.py -v
```

## 🐛 Troubleshooting

### Common Issues

#### "Scraping fails"
- **Cause**: G2/Capterra may have updated their HTML structure
- **Solution**: 
  - Check your internet connection
  - Try different tools
  - Check logs for detailed errors
  - Consider manual CSV upload (if implemented)

#### "xAI API errors"
- **Cause**: Invalid API key or quota exceeded
- **Solution**:
  - Verify API key is correct
  - Check API quota/limits at x.ai
  - Ensure internet connectivity

#### "No patterns found"
- **Cause**: Insufficient reviews or threshold too high
- **Solution**:
  - Try different tools
  - Lower `MIN_PATTERN_MENTIONS` in config.py
  - Use Semantic Analysis for better detection

#### "Performance issues"
- **Cause**: Too many tools or heavy analysis
- **Solution**:
  - Limit to 1-2 tools per run
  - Use Standard Analysis instead of Semantic
  - Check system resources (memory, CPU)

### Getting Help

1. **Check Documentation**
   - [README.md](README.md) - Project overview
   - [User Guide](docs/user_guide.md) - Usage instructions
   - [Developer Guide](docs/developer_guide.md) - Development setup
   - [API Reference](docs/api.md) - API documentation

2. **Review Logs**
   - Check console output for errors
   - Enable debug logging: `export LOG_LEVEL=DEBUG`

3. **Community**
   - Open an issue on GitHub
   - Check existing issues for solutions

## 📋 Next Steps

### For Users

1. ✅ Complete Quick Start
2. ✅ Run your first analysis
3. 📖 Read [User Guide](docs/user_guide.md) for advanced features
4. 🔍 Explore different tool combinations
5. 💾 Export and save your favorite insights

### For Developers

1. ✅ Complete Development Setup
2. ✅ Run tests successfully
3. 📖 Read [Developer Guide](docs/developer_guide.md)
4. 🔍 Explore the codebase structure
5. 🐛 Fix a bug or add a feature
6. 📝 Write tests for your changes
7. 🔄 Submit a pull request

### Learning Path

**Week 1: Basics**
- Understand the system architecture
- Run analyses and explore results
- Read core documentation

**Week 2: Intermediate**
- Modify configuration
- Understand scraping logic
- Explore pattern extraction

**Week 3: Advanced**
- Contribute code improvements
- Add new features
- Optimize performance

**Week 4: Expert**
- Design new components
- Lead feature development
- Mentor other contributors

## 📚 Additional Resources

### Documentation
- [README.md](README.md) - Project overview and quick start
- [User Guide](docs/user_guide.md) - Detailed usage instructions
- [Developer Guide](docs/developer_guide.md) - Development guidelines
- [API Reference](docs/api.md) - API documentation
- [Deployment Guide](DEPLOYMENT.md) - Deployment instructions

### External Resources
- [Streamlit Documentation](https://docs.streamlit.io/)
- [xAI API Documentation](https://x.ai/api)
- [Python Documentation](https://docs.python.org/3/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Project Files
- `app_v2.py` - Main Streamlit application
- `config.py` - Configuration and tool list
- `scraper/` - Web scraping modules
- `analyzer/` - Pattern extraction and AI analysis
- `utils/` - Utility modules
- `tests/` - Test suite

## 🎉 Welcome Aboard!

You're now ready to start using and contributing to the B2B Complaint-Driven Product Ideation App. Remember:

- **Start small**: Begin with 1-2 tools
- **Experiment**: Try different combinations
- **Learn**: Read the code and documentation
- **Contribute**: Share improvements and fixes
- **Have fun**: Building products that solve real problems!

If you have questions or need help, don't hesitate to:
- Check the documentation
- Review existing issues
- Open a new issue
- Ask the community

Happy analyzing! 🚀
