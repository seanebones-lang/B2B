"""Tests for CSRF protection"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from utils.csrf import CSRFProtection, get_csrf_protection


class TestCSRFProtection:
    """Test CSRF protection functionality"""
    
    def test_init(self):
        """Test CSRF protection initialization"""
        protection = CSRFProtection(secret_key="test_key_12345")
        assert protection.secret_key == "test_key_12345"
        assert protection.token_expiry == timedelta(hours=1)
    
    def test_generate_token(self):
        """Test token generation"""
        protection = CSRFProtection(secret_key="test_key_12345")
        session_id = "test_session_123"
        
        token = protection.generate_token(session_id)
        
        assert isinstance(token, str)
        assert len(token) == 64  # SHA256 hex digest length
    
    def test_validate_token_valid(self):
        """Test token validation with valid token"""
        protection = CSRFProtection(secret_key="test_key_12345")
        session_id = "test_session_123"
        
        token = protection.generate_token(session_id)
        is_valid = protection.validate_token(session_id, token)
        
        assert is_valid is True
    
    def test_validate_token_invalid(self):
        """Test token validation with invalid token"""
        protection = CSRFProtection(secret_key="test_key_12345")
        session_id = "test_session_123"
        
        protection.generate_token(session_id)
        is_valid = protection.validate_token(session_id, "invalid_token")
        
        assert is_valid is False
    
    def test_validate_token_expired(self):
        """Test token validation with expired token"""
        protection = CSRFProtection(secret_key="test_key_12345")
        protection.token_expiry = timedelta(seconds=-1)  # Expired immediately
        session_id = "test_session_123"
        
        token = protection.generate_token(session_id)
        is_valid = protection.validate_token(session_id, token)
        
        assert is_valid is False
    
    def test_get_token_for_session_new(self):
        """Test getting token for new session"""
        protection = CSRFProtection(secret_key="test_key_12345")
        session_id = "new_session"
        
        token = protection.get_token_for_session(session_id)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_get_token_for_session_existing(self):
        """Test getting token for existing session"""
        protection = CSRFProtection(secret_key="test_key_12345")
        session_id = "existing_session"
        
        token1 = protection.get_token_for_session(session_id)
        token2 = protection.get_token_for_session(session_id)
        
        # Should return same token if not expired
        assert token1 == token2
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        protection = CSRFProtection(secret_key="test_key_12345")
        protection.token_expiry = timedelta(seconds=-1)  # Expired immediately
        
        session_id = "expired_session"
        protection.generate_token(session_id)
        
        # Token should be expired
        protection.cleanup_expired_tokens()
        
        # Token should be removed
        token_data = getattr(protection, '_csrf_protection', {}).get('csrf_tokens', {})
        assert session_id not in token_data or len(token_data) == 0
    
    def test_get_csrf_protection_singleton(self):
        """Test singleton pattern"""
        protection1 = get_csrf_protection()
        protection2 = get_csrf_protection()
        assert protection1 is protection2
