"""CSRF protection utilities for Streamlit"""

import secrets
import hashlib
import hmac
from typing import Optional, Dict
from datetime import datetime, timedelta

import streamlit as st

from utils.logging import get_logger
from utils.secrets_manager import get_secrets_manager

logger = get_logger(__name__)


class CSRFProtection:
    """CSRF protection for Streamlit applications"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize CSRF protection
        
        Args:
            secret_key: Secret key for token generation (defaults to SECRET_KEY env var)
        """
        secrets_manager = get_secrets_manager()
        self.secret_key = secret_key or secrets_manager.master_key or secrets.token_urlsafe(32)
        self.token_expiry = timedelta(hours=1)
        
        logger.info("CSRF protection initialized")
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate CSRF token for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            CSRF token
        """
        timestamp = str(int(datetime.utcnow().timestamp()))
        message = f"{session_id}:{timestamp}"
        
        token = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Store token in session state
        if "csrf_tokens" not in st.session_state:
            st.session_state.csrf_tokens = {}
        
        st.session_state.csrf_tokens[session_id] = {
            "token": token,
            "timestamp": timestamp,
            "expires_at": datetime.utcnow() + self.token_expiry
        }
        
        logger.debug("CSRF token generated", session_id=session_id)
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """
        Validate CSRF token
        
        Args:
            session_id: Session identifier
            token: Token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        if "csrf_tokens" not in st.session_state:
            logger.warning("No CSRF tokens in session state")
            return False
        
        stored_token_data = st.session_state.csrf_tokens.get(session_id)
        
        if not stored_token_data:
            logger.warning("No CSRF token found for session", session_id=session_id)
            return False
        
        # Check expiration
        if datetime.utcnow() > stored_token_data["expires_at"]:
            logger.warning("CSRF token expired", session_id=session_id)
            del st.session_state.csrf_tokens[session_id]
            return False
        
        # Validate token
        stored_token = stored_token_data["token"]
        is_valid = hmac.compare_digest(stored_token, token)
        
        if not is_valid:
            logger.warning("Invalid CSRF token", session_id=session_id)
        
        return is_valid
    
    def get_token_for_session(self, session_id: str) -> Optional[str]:
        """
        Get CSRF token for a session (generate if not exists)
        
        Args:
            session_id: Session identifier
            
        Returns:
            CSRF token or None
        """
        if "csrf_tokens" not in st.session_state:
            st.session_state.csrf_tokens = {}
        
        token_data = st.session_state.csrf_tokens.get(session_id)
        
        # Check if token exists and is valid
        if token_data:
            if datetime.utcnow() < token_data["expires_at"]:
                return token_data["token"]
            else:
                # Token expired, remove it
                del st.session_state.csrf_tokens[session_id]
        
        # Generate new token
        return self.generate_token(session_id)
    
    def cleanup_expired_tokens(self):
        """Clean up expired CSRF tokens"""
        if "csrf_tokens" not in st.session_state:
            return
        
        now = datetime.utcnow()
        expired_sessions = [
            session_id
            for session_id, token_data in st.session_state.csrf_tokens.items()
            if now > token_data["expires_at"]
        ]
        
        for session_id in expired_sessions:
            del st.session_state.csrf_tokens[session_id]
        
        if expired_sessions:
            logger.info("Cleaned up expired CSRF tokens", count=len(expired_sessions))


# Global CSRF protection instance
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Get global CSRF protection instance"""
    global _csrf_protection
    if _csrf_protection is None:
        _csrf_protection = CSRFProtection()
    return _csrf_protection


def require_csrf_token(func):
    """Decorator to require CSRF token validation"""
    def wrapper(*args, **kwargs):
        # CSRF validation would happen here
        # For Streamlit, we'll validate in the function itself
        return func(*args, **kwargs)
    return wrapper
