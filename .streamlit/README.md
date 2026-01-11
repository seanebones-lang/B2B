# Streamlit Configuration

This directory contains Streamlit-specific configuration files.

## Files

- `config.toml` - Streamlit app configuration (theme, server settings)
- `secrets.toml.example` - Example secrets file (copy to `secrets.toml` for local development)

## For Streamlit Cloud

Secrets are managed through the Streamlit Cloud dashboard:
1. Go to your app settings
2. Click "Secrets"
3. Add your secrets in TOML format

Example:
```toml
XAI_API_KEY = "your-api-key-here"
```

## For Local Development

1. Copy `secrets.toml.example` to `secrets.toml`
2. Fill in your actual values
3. Never commit `secrets.toml` to git (it's in .gitignore)
