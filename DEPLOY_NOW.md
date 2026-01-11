# Deploy Now - Quick Guide

**Status:** ✅ Code is ready for deployment  
**Repository:** https://github.com/seanebones-lang/B2B  
**Branch:** main

---

## 🚀 Option 1: Streamlit Cloud (Recommended - Free & Easy)

### Quick Steps:

1. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App:**
   - Click "New app"
   - Repository: `seanebones-lang/B2B`
   - Branch: `main`
   - Main file path: `app.py` (or `app_v2.py` for enhanced version)
   - Python version: `3.11`

3. **Add Secrets:**
   - Click "Advanced settings" → "Secrets"
   - Add:
   ```toml
   XAI_API_KEY = "your-xai-api-key-here"
   ```
   - Optional (for production):
   ```toml
   ENCRYPTION_SALT = "your-base64-encoded-salt"
   DB_ENCRYPTION_SALT = "your-base64-encoded-salt"
   DATABASE_URL = "sqlite:///./data/app.db"
   LOG_LEVEL = "INFO"
   ```

4. **Deploy:**
   - Click "Deploy!"
   - Wait 2-3 minutes
   - Your app will be live!

**Your app URL will be:** `https://your-app-name.streamlit.app`

---

## 🐳 Option 2: Docker Deployment

### Local Docker Deployment:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t b2b-analyzer .
docker run -p 8501:8501 \
  -e XAI_API_KEY=your-api-key \
  -e ENCRYPTION_SALT=your-salt \
  -e DB_ENCRYPTION_SALT=your-salt \
  b2b-analyzer
```

**Access at:** http://localhost:8501

### Production Docker Deployment:

1. **Set environment variables:**
   ```bash
   export XAI_API_KEY=your-api-key
   export ENCRYPTION_SALT=$(python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(16)).decode())")
   export DB_ENCRYPTION_SALT=$(python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(16)).decode())")
   ```

2. **Deploy with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Or deploy to cloud platform:**
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances
   - DigitalOcean App Platform
   - Heroku (with Docker support)

---

## ✅ Post-Deployment Checklist

- [ ] App loads successfully
- [ ] Can enter/configure API key
- [ ] Can select tools
- [ ] Analysis runs without errors
- [ ] Results display correctly
- [ ] Export functions work
- [ ] Health endpoint accessible (if using app_v2.py)

---

## 🔧 Troubleshooting

### Streamlit Cloud Issues:

**App won't start:**
- Check logs: Click "Manage app" → "Logs"
- Verify `requirements.txt` has all dependencies
- Ensure Python version is 3.10+

**API Key issues:**
- Verify secret is named exactly `XAI_API_KEY`
- Check API key is valid at https://x.ai/api
- Ensure no extra spaces in secret value

**Import errors:**
- Check logs for missing modules
- Some optional dependencies may need to be removed
- Verify all imports are in `requirements.txt`

### Docker Issues:

**Build fails:**
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check Docker daemon is running

**Container won't start:**
- Check logs: `docker-compose logs app`
- Verify environment variables are set
- Check port 8501 is available

---

## 📝 Notes

- **Streamlit Cloud Free Tier:** 1 app per account, public only
- **Resource Limits:** May need optimization for free tier
- **Secrets:** Never commit secrets to GitHub
- **Updates:** Push to GitHub to auto-deploy updates (Streamlit Cloud)
- **Docker:** Better for production, more control, requires hosting

---

## 🎯 Recommended: Streamlit Cloud

For quick deployment, use **Streamlit Cloud**:
- ✅ Free
- ✅ Easy setup
- ✅ Auto-deploys on git push
- ✅ No server management
- ✅ HTTPS included

**Ready to deploy!** 🚀
