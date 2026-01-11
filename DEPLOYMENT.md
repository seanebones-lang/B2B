# Deployment Guide

This guide covers deploying the B2B Complaint Analyzer to Streamlit Cloud.

---

## Prerequisites

- GitHub account
- Streamlit Cloud account (free at [streamlit.io/cloud](https://streamlit.io/cloud))
- xAI API key ([get one here](https://x.ai/api))

---

## Streamlit Cloud Deployment

### Step 1: Prepare Your Repository

1. **Ensure your code is on GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Verify main file:**
   - The app uses `app.py` as the main file (or `app_v2.py` if preferred)
   - Ensure `requirements.txt` is up to date
   - Ensure `.streamlit/config.toml` exists (optional but recommended)

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App:**
   - Click "New app"
   - Select your GitHub repository
   - Choose the branch (usually `main`)

3. **Configure App:**
   - **Main file path:** `app.py` (or `app_v2.py`)
   - **Python version:** 3.11 (or 3.10/3.12)
   - **App URL:** Choose your custom URL (optional)

4. **Add Secrets:**
   - Click "Advanced settings" → "Secrets"
   - Add the following secrets:
   ```toml
   XAI_API_KEY = "your-xai-api-key-here"
   ```
   - Optionally add:
   ```toml
   DATABASE_URL = "sqlite:///./data/app.db"
   LOG_LEVEL = "INFO"
   ENVIRONMENT = "production"
   ```

5. **Deploy:**
   - Click "Deploy!"
   - Wait for deployment to complete
   - Your app will be available at `https://your-app-name.streamlit.app`

---

## Local Deployment

### Option 1: Direct Streamlit Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
# or
streamlit run app_v2.py
```

The app will open at `http://localhost:8501`

### Option 2: Docker Deployment

```bash
# Build Docker image
docker build -t b2b-analyzer .

# Run container
docker run -p 8501:8501 \
  -e XAI_API_KEY=your-api-key \
  b2b-analyzer
```

### Option 3: Docker Compose

```bash
# Create .env file
echo "XAI_API_KEY=your-api-key" > .env

# Run with docker-compose
docker-compose up -d
```

---

## Environment Variables

### Required
- `XAI_API_KEY` - Your xAI API key (required for AI analysis)

### Optional
- `DATABASE_URL` - Database connection string (default: SQLite)
- `LOG_LEVEL` - Logging level (default: INFO)
- `ENVIRONMENT` - Environment name (default: development)
- `RATE_LIMIT_ENABLED` - Enable rate limiting (default: true)
- `RATE_LIMIT_REQUESTS_PER_MINUTE` - Rate limit (default: 60)
- `SECRET_KEY` - Secret key for security (generate random string)

---

## Post-Deployment Checklist

- [ ] Verify app loads correctly
- [ ] Test API key input
- [ ] Test tool selection
- [ ] Test analysis workflow
- [ ] Verify error handling
- [ ] Check logs for errors
- [ ] Test export functionality
- [ ] Verify health endpoint (if using app_v2.py)

---

## Troubleshooting

### App Won't Start
- Check `requirements.txt` is up to date
- Verify Python version compatibility (3.10+)
- Check Streamlit Cloud logs for errors

### API Key Issues
- Verify `XAI_API_KEY` is set in secrets
- Check API key format (should be 40+ characters)
- Verify API key is valid at [x.ai/api](https://x.ai/api)

### Import Errors
- Ensure all dependencies are in `requirements.txt`
- Check for missing modules
- Verify Python version matches requirements

### Database Issues
- Ensure `data/` directory exists (for SQLite)
- Check database permissions
- Verify `DATABASE_URL` if using external database

---

## Production Considerations

### Security
- ✅ Never commit API keys to repository
- ✅ Use Streamlit secrets for sensitive data
- ✅ Enable XSRF protection (already enabled in config.toml)
- ✅ Use HTTPS (automatic on Streamlit Cloud)

### Performance
- ✅ Enable caching (already implemented)
- ✅ Use async operations (already implemented)
- ✅ Monitor resource usage
- ✅ Set appropriate rate limits

### Monitoring
- ✅ Check Streamlit Cloud logs regularly
- ✅ Monitor API usage
- ✅ Track error rates
- ✅ Monitor performance metrics

---

## Streamlit Cloud Limits

- **Free Tier:**
  - 1 app per GitHub account
  - Public apps only
  - Resource limits apply

- **Team Tier:**
  - Multiple apps
  - Private apps
  - More resources

---

## Support

For issues or questions:
- Check [Streamlit Cloud docs](https://docs.streamlit.io/streamlit-cloud)
- Review application logs in Streamlit Cloud dashboard
- Check GitHub issues

---

**Deployment Status:** ✅ Ready for Streamlit Cloud
