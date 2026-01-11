#!/bin/bash
# Quick deployment script for Streamlit Cloud

set -e

echo "🚀 Preparing for Streamlit Cloud Deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "⚠️  Git not initialized. Initializing..."
    git init
    git add .
    git commit -m "Initial commit for Streamlit Cloud deployment"
fi

# Check if .streamlit directory exists
if [ ! -d ".streamlit" ]; then
    echo "📁 Creating .streamlit directory..."
    mkdir -p .streamlit
fi

# Check if config.toml exists
if [ ! -f ".streamlit/config.toml" ]; then
    echo "📝 Creating .streamlit/config.toml..."
    cat > .streamlit/config.toml << EOF
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
EOF
fi

# Check if secrets.toml.example exists
if [ ! -f ".streamlit/secrets.toml.example" ]; then
    echo "📝 Creating .streamlit/secrets.toml.example..."
    cat > .streamlit/secrets.toml.example << EOF
# Streamlit Secrets Configuration
# Copy this file to .streamlit/secrets.toml and fill in your values
# For Streamlit Cloud, add these as secrets in the dashboard

XAI_API_KEY = "your-xai-api-key-here"
EOF
fi

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Check main app file
if [ ! -f "app.py" ] && [ ! -f "app_v2.py" ]; then
    echo "❌ No app.py or app_v2.py found!"
    exit 1
fi

echo ""
echo "✅ Preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Push your code to GitHub:"
echo "   git remote add origin <your-github-repo-url>"
echo "   git push -u origin main"
echo ""
echo "2. Go to https://share.streamlit.io"
echo "3. Click 'New app' and connect your repository"
echo "4. Set main file path to: app.py (or app_v2.py)"
echo "5. Add XAI_API_KEY in secrets section"
echo "6. Deploy!"
echo ""
echo "📚 See DEPLOYMENT.md for detailed instructions"
