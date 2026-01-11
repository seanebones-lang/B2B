"""Security utilities: input validation, sanitization, and API key management"""

import re
import html
from typing import Any, Dict, Optional
from functools import wraps
import hashlib
import hmac
import os
from datetime import datetime, timedelta

import streamlit as st
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    
    secret_key: str = Field(default="", env="SECRET_KEY")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class InputValidator:
    """Input validation and sanitization utilities"""
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(\\;)|(\|)|(\\|)|(\*)|(\\*)|(%)|(\\%)|(xp_)|(sp_))",
        r"(union|select|insert|update|delete|drop|create|alter|exec|execute)",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input to prevent XSS and injection attacks
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # HTML escape to prevent XSS
        sanitized = html.escape(value)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Truncate if needed
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> bool:
        """
        Validate API key format
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # xAI API keys are typically 40+ characters, alphanumeric
        if len(api_key) < 20:
            return False
        
        # Check for suspicious patterns
        if any(pattern in api_key.lower() for pattern in ['script', 'javascript', '<', '>']):
            return False
        
        return True
    
    @classmethod
    def validate_tool_name(cls, tool_name: str) -> bool:
        """
        Validate tool name input
        
        Args:
            tool_name: Tool name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not tool_name or not isinstance(tool_name, str):
            return False
        
        # Only allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tool_name):
            return False
        
        if len(tool_name) > 100:
            return False
        
        return True
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """
        Detect potential XSS attacks
        
        Args:
            value: String to check
            
        Returns:
            True if XSS pattern detected, False otherwise
        """
        value_lower = value.lower()
        return any(re.search(pattern, value_lower, re.IGNORECASE | re.DOTALL) 
                   for pattern in cls.XSS_PATTERNS)
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """
        Detect potential SQL injection attempts
        
        Args:
            value: String to check
            
        Returns:
            True if SQL injection pattern detected, False otherwise
        """
        value_lower = value.lower()
        return any(re.search(pattern, value_lower, re.IGNORECASE) 
                   for pattern in cls.SQL_INJECTION_PATTERNS)


class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.settings = SecuritySettings()
        self._api_key_cache: Dict[str, datetime] = {}
    
    def get_api_key(self, source: str = "streamlit") -> Optional[str]:
        """
        Securely retrieve API key from environment or Streamlit secrets
        
        Args:
            source: Source to retrieve from ("env" or "streamlit")
            
        Returns:
            API key if found and valid, None otherwise
        """
        api_key = None
        
        if source == "streamlit":
            try:
                api_key = st.secrets.get("XAI_API_KEY") or os.getenv("XAI_API_KEY")
            except Exception:
                api_key = os.getenv("XAI_API_KEY")
        else:
            api_key = os.getenv("XAI_API_KEY")
        
        if api_key and InputValidator.validate_api_key(api_key):
            return api_key
        
        return None
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Hash API key for storage/audit (one-way)
        
        Args:
            api_key: API key to hash
            
        Returns:
            Hashed API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_request_signature(self, data: str, signature: str) -> bool:
        """
        Verify request signature using HMAC
        
        Args:
            data: Request data
            signature: Provided signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.settings.secret_key:
            return False
        
        expected_signature = hmac.new(
            self.settings.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def sanitize_user_input(self, value: Any) -> Any:
        """
        Sanitize user input based on type
        
        Args:
            value: Input value to sanitize
            
        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            # Check for XSS and SQL injection
            if InputValidator.detect_xss(value):
                raise ValueError("Potentially malicious input detected (XSS)")
            if InputValidator.detect_sql_injection(value):
                raise ValueError("Potentially malicious input detected (SQL Injection)")
            
            return InputValidator.sanitize_string(value)
        elif isinstance(value, (list, tuple)):
            return [self.sanitize_user_input(item) for item in value]
        elif isinstance(value, dict):
            return {k: self.sanitize_user_input(v) for k, v in value.items()}
        else:
            return value


def require_api_key(func):
    """Decorator to require valid API key"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        security_manager = SecurityManager()
        api_key = security_manager.get_api_key()
        
        if not api_key:
            raise ValueError("API key is required but not found or invalid")
        
        return func(*args, **kwargs)
    
    return wrapper
