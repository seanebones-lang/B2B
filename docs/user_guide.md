# User Guide

## Getting Started

### Prerequisites

- Python 3.10 or higher
- xAI API key ([Get one here](https://x.ai/api))

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd B2B
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your XAI_API_KEY
```

### Running the Application

```bash
streamlit run app_v2.py
```

The application will open in your browser at `http://localhost:8501`

## Using the Application

### Step 1: Configure API Key

1. Enter your xAI API key in the sidebar
2. The key is stored securely in your session (not persisted)

### Step 2: Select Tools

1. Choose 1-3 B2B SaaS tools to analyze from the dropdown
2. Recommended: Start with 1-2 tools for faster results

### Step 3: Choose Analysis Method

- **Semantic Analysis**: Uses advanced NLP for better pattern detection (recommended)
- **Standard Analysis**: Uses TF-IDF + K-Means clustering (faster, less accurate)

### Step 4: Run Analysis

1. Click "Run Analysis"
2. The system will:
   - Scrape reviews from G2 and Capterra
   - Extract complaint patterns
   - Generate AI-powered product ideas
   - Create actionable roadmaps

### Step 5: Review Results

Explore the results in three tabs:
- **Summary**: Overview of analysis results
- **Per-Tool Breakdown**: Detailed analysis for each tool
- **Top 3 Opportunities**: Best product ideas with roadmaps

### Step 6: Export Results

- **Markdown**: Download as `.md` file
- **JSON**: Download as `.json` file

## Understanding Results

### Complaint Patterns

Patterns are identified based on:
- Frequency (how many reviews mention it)
- Impact (how it affects workflows)
- Keywords (missing features, wishes, blockers)

### Product Ideas

Each idea includes:
- **Name**: Catchy product name
- **Value Prop**: One-sentence value proposition
- **Target**: Target audience
- **MVP Scope**: Core features for MVP
- **Monetization**: Pricing strategy

### Roadmaps

4-week solo founder roadmaps include:
- **Week 1**: Validation (surveys, interviews)
- **Week 2**: MVP Development (landing page, core features)
- **Week 3**: Launch (marketing, initial users)
- **Week 4**: Iteration (feedback, improvements)

## Troubleshooting

### Scraping Fails

- G2/Capterra may have updated their HTML structure
- Check your internet connection
- Try selecting different tools
- Check logs for detailed error messages

### API Errors

- Verify your API key is correct
- Check your API quota/limits
- Ensure you have internet connectivity
- Check logs for detailed error messages

### No Patterns Found

- Try selecting different tools
- Increase review count threshold in config.py
- Check if reviews contain complaint keywords
- Try semantic analysis for better results

### Performance Issues

- Limit to 1-2 tools per run
- Use standard analysis instead of semantic
- Check system resources (memory, CPU)
- Review cached data in database

## Best Practices

1. **Start Small**: Begin with 1-2 tools
2. **Use Semantic Analysis**: Better pattern detection
3. **Review Cached Data**: System caches reviews to avoid re-scraping
4. **Export Results**: Save important analyses
5. **Check Health**: Visit `/health` endpoint for system status

## Advanced Features

### Caching

The system caches scraped reviews to avoid re-scraping:
- Reviews are cached for 24 hours (configurable)
- Cached data is used automatically
- Clear cache by restarting the application

### Database Persistence

Analysis results are saved to database:
- Reviews are persisted for future use
- Analysis results are stored with session ID
- GDPR-compliant data retention (90 days default)

### Rate Limiting

The system includes rate limiting:
- Prevents API abuse
- Configurable requests per minute
- Automatic retry with exponential backoff

## Support

For issues or questions:
- Check the [README](../README.md)
- Review [Developer Guide](developer_guide.md)
- Open an issue on GitHub
