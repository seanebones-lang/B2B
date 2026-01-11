# B2B Complaint Analyzer Documentation

Welcome to the B2B Complaint Analyzer documentation.

## Documentation Structure

- **[Onboarding Guide](../ONBOARDING.md)** - Start here! Complete guide for new users and developers
- [API Reference](api.md) - Complete API documentation
- [User Guide](user_guide.md) - How to use the application
- [Developer Guide](developer_guide.md) - Development setup and guidelines
- [Architecture](architecture.md) - System architecture overview

## Quick Start

### For Users

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables (see `.env.example`)
3. Run the application: `streamlit run app_v2.py`
4. See [User Guide](user_guide.md) for detailed instructions

### For Developers

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest tests/`
4. See [Developer Guide](developer_guide.md) for detailed setup

## Features

- **Automated Review Scraping**: Scrapes 1-2 star reviews from G2 and Capterra
- **Pattern Detection**: Identifies complaint patterns using keyword matching and ML clustering
- **AI-Powered Analysis**: Uses xAI Grok to analyze patterns and generate product ideas
- **Actionable Roadmaps**: Creates 4-week solo founder roadmaps for top opportunities

## Support

For issues, questions, or contributions, please see the main [README](../README.md).
