"""Security headers middleware for Streamlit"""

from typing import Dict


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses
    
    Returns:
        Dictionary of security headers
    """
    return {
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.x.ai; "
            "frame-ancestors 'none';"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=()"
        )
    }


def apply_security_headers():
    """
    Apply security headers to Streamlit app
    
    Note: Streamlit doesn't support custom headers directly,
    but this can be used with reverse proxy or custom server
    """
    headers = get_security_headers()
    # In production, these would be set via reverse proxy (nginx, etc.)
    # or custom Streamlit server configuration
    return headers
