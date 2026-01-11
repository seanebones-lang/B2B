# Quick Deployment Guide - Streamlit Cloud

## 🚀 Fast Track Deployment

### Prerequisites
- ✅ GitHub repository with your code
- ✅ Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- ✅ xAI API key ([get one here](https://x.ai/api))

---

## Step-by-Step Deployment

### 1. Prepare Your Code
```bash
# Run the deployment preparation script
./streamlit_deploy.sh

# Or manually ensure:
# - .streamlit/config.toml exists
# - requirements.txt is up to date
# - app.py or app_v2.py is ready
```

### 2. Push to GitHub
```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### 3. Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io
   - Sign in with GitHub

2. **Create New App:**
   - Click "New app"
   - Select repository: `your-username/B2B` (or your repo name)
   - Branch: `main`

3. **Configure:**
   - **Main file path:** `app.py` (or `app_v2.py` for enhanced version)
   - **Python version:** 3.11 (or 3.10/3.12)

4. **Add Secrets:**
   Click "Advanced settings" → "Secrets" and add:
   ```toml
   XAI_API_KEY = "your-actual-xai-api-key-here"
   ```

5. **Deploy:**
   - Click "Deploy!"
   - Wait 2-3 minutes for deployment
   - Your app will be live at: `https://your-app-name.streamlit.app`

---

## ✅ Post-Deployment Checklist

- [ ] App loads successfully
- [ ] Can enter API key
- [ ] Can select tools
- [ ] Analysis runs without errors
- [ ] Results display correctly
- [ ] Export functions work

---

## 🔧 Troubleshooting

### App Won't Start
- Check Streamlit Cloud logs (click "Manage app" → "Logs")
- Verify `requirements.txt` has all dependencies
- Ensure Python version is 3.10+

### API Key Issues
- Verify secret is named exactly `XAI_API_KEY`
- Check API key is valid at [x.ai/api](https://x.ai/api)
- Ensure no extra spaces in secret value

### Import Errors
- Check logs for missing modules
- Verify all dependencies in `requirements.txt`
- Some optional dependencies may need to be removed for Streamlit Cloud

---

## 📝 Notes

- **Free Tier:** 1 app per account, public only
- **Resource Limits:** May need to optimize for free tier
- **Secrets:** Never commit secrets to GitHub
- **Updates:** Push to GitHub to auto-deploy updates

---

## 🎯 Your App Will Be Available At:

`https://your-app-name.streamlit.app`

Replace `your-app-name` with the name you choose during deployment.

---

**Ready to deploy!** 🚀
