# B2B Complaint-Driven Product Ideation App

A Streamlit web application that extracts unmet needs from 1-2 star reviews of popular B2B SaaS tools, identifies high-demand patterns, and uses xAI's Grok to generate actionable product ideas with 4-week roadmaps.

## 🎯 What This System Does

This application automates the process of complaint-driven product discovery by:

1. **Scraping Negative Reviews**: Automatically collects 1-2 star reviews from G2.com and Capterra for popular B2B SaaS tools
2. **Identifying Pain Patterns**: Uses keyword matching and machine learning clustering to find recurring complaint themes
3. **AI-Powered Analysis**: Leverages xAI's Grok to analyze patterns, assess impact, and generate novel product ideas
4. **Actionable Roadmaps**: Creates detailed 4-week solo founder roadmaps for the top opportunities

The system treats every complaint as a "pre-paid invoice" from future customers, helping entrepreneurs identify validated market needs and build products that solve real problems.

## Features

- 🔍 **Automated Review Scraping**: Scrapes 1-2 star reviews from G2.com and Capterra
- 📊 **Pattern Detection**: Identifies complaint patterns using keyword matching and ML clustering
- 🤖 **AI-Powered Analysis**: Uses xAI Grok to analyze patterns and generate product ideas
- 🚀 **Actionable Roadmaps**: Creates 4-week solo founder roadmaps for top opportunities
- 📥 **Export Options**: Export results as Markdown or JSON

## Quick Start

> **New to the project?** Check out the [Onboarding Guide](ONBOARDING.md) for a comprehensive introduction!

### Prerequisites

- Python 3.8+
- xAI API key ([Get one here](https://x.ai/api))

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd B2B
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Streamlit secrets (optional, for production):
Create `.streamlit/secrets.toml`:
```toml
XAI_API_KEY = "your-api-key-here"
```

### Running Locally

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Deployment to Streamlit Cloud

**Quick Deploy:**
```bash
./streamlit_deploy.sh
```

**Manual Steps:**
1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io)
3. Click "New app"
4. Connect your GitHub repository
5. Set the main file path to `app.py` (or `app_v2.py` for enhanced version)
6. Add your `XAI_API_KEY` in the secrets section:
   ```toml
   XAI_API_KEY = "your-xai-api-key-here"
   ```
7. Deploy!

**For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

## Usage

1. **Enter xAI API Key**: Input your API key in the sidebar (or use secrets.toml)
2. **Select Tools**: Choose 1-3 B2B SaaS tools to analyze from the dropdown
3. **Run Analysis**: Click "Run Analysis" to:
   - Scrape reviews from G2 and Capterra
   - Extract complaint patterns
   - Generate AI-powered product ideas
   - Create actionable roadmaps
4. **Review Results**: Explore the Summary, Per-Tool Breakdown, and Top 3 Opportunities tabs
5. **Export**: Download results as Markdown or JSON

## Supported Tools

The app comes pre-configured with 10 popular B2B SaaS tools:

- Salesforce (CRM)
- HubSpot (CRM/Marketing)
- Slack (Comms)
- Asana (PM)
- Notion (Productivity)
- Zoom (Video)
- Intercom (Customer Support)
- Zendesk (Customer Support)
- Workday (HRIS)
- BambooHR (HRIS)

## Project Structure

```
B2B/
├── app.py                 # Main Streamlit application
├── config.py              # Tool list, keywords, settings
├── scraper/
│   ├── __init__.py
│   ├── base.py            # Base scraper with anti-detection
│   ├── g2_scraper.py      # G2.com review scraper
│   └── capterra_scraper.py # Capterra review scraper
├── analyzer/
│   ├── __init__.py
│   ├── pattern_extractor.py  # Keyword matching & clustering
│   └── xai_client.py      # xAI Grok API integration
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── README.md
```

## How It Works

1. **Review Scraping**: Uses BeautifulSoup to scrape reviews with anti-detection (rotating user agents, delays)
2. **Pattern Extraction**: 
   - Keyword matching for pain categories (missing features, wishes, blockers)
   - ML clustering (TF-IDF + K-Means) to group similar complaints
   - Frequency filtering (5+ mentions or 15%+ of reviews)
3. **AI Analysis**: xAI Grok analyzes patterns and generates:
   - Top pain patterns with impact analysis
   - Product ideas (standalone apps, plugins, integrations)
   - 4-week solo founder roadmaps
4. **Report Generation**: Structured output with actionable insights

## Configuration

Edit `config.py` to:
- Add/modify B2B tools
- Adjust pain keywords
- Change pattern detection thresholds
- Modify scraping settings

## Limitations & Notes

- **Scraping**: G2 and Capterra may block scrapers. The app includes error handling and fallbacks.
- **Rate Limiting**: Built-in delays prevent overwhelming servers. Limit to 1-3 tools per run.
- **API Costs**: xAI API usage depends on review volume. Monitor your usage.
- **Review Quality**: Results depend on review availability and quality.

## Troubleshooting

**Scraping fails**: 
- G2/Capterra may have updated their HTML structure
- Try manual CSV upload (feature to be added)
- Check your internet connection

**xAI API errors**:
- Verify your API key is correct
- Check your API quota/limits
- Ensure you have internet connectivity

**No patterns found**:
- Try selecting different tools
- Increase review count threshold in config.py
- Check if reviews contain complaint keywords

## Contributing

Contributions welcome! Areas for improvement:
- Better scraping reliability
- Manual CSV upload fallback
- More sophisticated pattern detection
- Additional export formats
- UI/UX enhancements

## Legal

**© 2026 NextEleven Studios. S. McDonnell, CTO. All Rights Reserved.**

**No unauthorized viewing or use permitted under penalty of law.**

For complete legal documentation, see the [legal/](legal/) directory:

- [Privacy Policy](legal/PRIVACY_POLICY.md) - Data collection and privacy practices
- [Terms of Use](legal/TERMS_OF_USE.md) - Terms governing use of the Service
- [End User License Agreement (EULA)](legal/EULA.md) - Software license terms
- [Copyright Notice](legal/COPYRIGHT.md) - Copyright ownership and protection
- [Trademark Notice](legal/TRADEMARK.md) - Trademark ownership and usage
- [Legal Notice](legal/LEGAL.md) - Comprehensive legal information

## License

See LICENSE file for details.

## Disclaimer

This tool is for research and ideation purposes. Always respect website terms of service and rate limits when scraping. Use responsibly.

**By using this software, you agree to be bound by the Terms of Use, EULA, and Privacy Policy.**
