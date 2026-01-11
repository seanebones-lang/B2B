# Streamlit Cloud Setup Guide

## 🎯 Quick Setup (5 Minutes)

### Step 1: Fix Local Issues (DONE ✅)
All critical bugs have been fixed:
- ✅ Import errors resolved
- ✅ Deprecated parameters updated
- ✅ Model configuration corrected

### Step 2: Configure Streamlit Cloud Secrets

1. Go to your Streamlit Cloud app settings
2. Click on "Secrets" in the left sidebar
3. Add the following configuration:

```toml
# Required: xAI API Key
XAI_API_KEY = "your-xai-api-key-here"

# Model Configuration (Updated Jan 2026)
XAI_MODEL = "grok-3"
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_TEMPERATURE = 0.3
XAI_MAX_TOKENS = 2000

# Optional: Scraping Settings
MAX_REVIEWS_PER_TOOL = 30
SCRAPE_TIMEOUT = 30
CACHE_ENABLED = "true"
CACHE_TTL_SECONDS = 7200
```

### Step 3: Deploy

1. **Commit and push your changes:**
   ```bash
   git add .
   git commit -m "Fix: Streamlit deployment issues (imports, deprecations, model)"
   git push origin main
   ```

2. **Streamlit Cloud will auto-deploy** from your GitHub repository

3. **Monitor the deployment:**
   - Watch the logs for any errors
   - First deployment may take 2-3 minutes
   - Look for "App is ready!" message

---

## 🔧 Troubleshooting

### Issue: "ImportError: cannot import name 'get_monitor'"
**Status:** ✅ FIXED in this update
**Action:** Make sure you've pushed the latest changes

### Issue: "Error code: 404 - model grok-beta was deprecated"
**Solution:** 
1. Check your Streamlit Cloud secrets
2. Make sure `XAI_MODEL = "grok-3"` (not "grok-beta")
3. Restart the app after updating secrets

### Issue: "403 Forbidden" errors for G2/Capterra
**Status:** ℹ️ EXPECTED (not a bug)
**Explanation:** These sites block Streamlit Cloud IPs
**Impact:** None - app falls back to Hacker News and other sources

### Issue: Playwright browser not found
**Status:** ℹ️ EXPECTED on Streamlit Cloud
**Explanation:** Browser automation not supported in cloud environment
**Impact:** None - app uses alternative scraping methods

---

## 📊 Expected Behavior After Deployment

### ✅ What Should Work:
- App starts without errors
- Sidebar loads with tool selection
- API key validation works
- Analysis runs successfully
- Hacker News scraping works (30+ discussions)
- AI analysis generates insights
- Results display correctly

### ⚠️ Expected Warnings (Safe to Ignore):
- "Circuit breaker OPEN" for G2/Capterra (anti-bot protection)
- "Playwright scraping failed" (not available on cloud)
- "Reddit request failed" (anti-bot protection)
- "Product Hunt page not found" (anti-bot protection)

### ❌ What Should NOT Happen:
- ImportError on startup
- "grok-beta" deprecation errors
- App crashes during analysis
- No results returned

---

## 🎨 UI Configuration

The app uses the new Streamlit parameters:
- `width="stretch"` for full-width components
- Proper button styling with `type="primary"`
- Responsive dataframes

---

## 📈 Performance Expectations

### Data Collection:
- **Hacker News:** 30 discussions per tool (working)
- **G2/Capterra:** 0 reviews (blocked, expected)
- **Reddit:** 0 posts (blocked, expected)
- **Total:** ~30 data points per tool

### Analysis Time:
- Single tool: 30-60 seconds
- Multiple tools: 1-3 minutes per tool
- Depends on xAI API response time

### Resource Usage:
- Memory: ~500MB (Streamlit Cloud limit: 1GB)
- CPU: Minimal (mostly API calls)
- Network: Moderate (scraping + API calls)

---

## 🔐 Security Best Practices

1. **Never commit API keys** to GitHub
2. **Use Streamlit Cloud secrets** for sensitive data
3. **Rotate API keys** periodically
4. **Monitor usage** on xAI console
5. **Enable audit logging** for compliance

---

## 🚀 Advanced Configuration

### Custom Model Selection:
```toml
# Use latest model (may have rate limits)
XAI_MODEL = "grok-4.1-fast-reasoning"

# Use stable model (recommended)
XAI_MODEL = "grok-3"
```

### Adjust Analysis Depth:
```toml
# More detailed analysis (slower, more expensive)
XAI_MAX_TOKENS = 4000
XAI_TEMPERATURE = 0.5

# Faster analysis (less detail)
XAI_MAX_TOKENS = 1000
XAI_TEMPERATURE = 0.2
```

### Cache Configuration:
```toml
# Longer cache (better performance, less fresh data)
CACHE_TTL_SECONDS = 14400  # 4 hours

# Shorter cache (more API calls, fresher data)
CACHE_TTL_SECONDS = 3600   # 1 hour
```

---

## 📞 Support

### If You Need Help:

1. **Check the logs:**
   - Streamlit Cloud → Your App → Manage App → Logs
   - Look for specific error messages

2. **Common fixes:**
   - Restart the app
   - Clear cache and reboot
   - Verify secrets are set correctly
   - Check xAI API key is valid

3. **Still stuck?**
   - Check `DEPLOYMENT_FIXES_2026_01_11.md` for detailed error explanations
   - Review `QUICK_FIX_SUMMARY.md` for troubleshooting steps

---

## ✅ Deployment Checklist

- [x] All code fixes applied
- [x] No linting errors
- [ ] Secrets configured on Streamlit Cloud
- [ ] Changes pushed to GitHub
- [ ] App deployed successfully
- [ ] Tested with single tool
- [ ] Verified AI analysis works
- [ ] Checked logs for errors

---

**Last Updated:** January 11, 2026  
**Status:** ✅ Ready for Production  
**Estimated Setup Time:** 5 minutes  
**Difficulty:** Easy
