"""Tests for security utilities"""

import pytest
from utils.security import InputValidator, SecurityManager


class TestInputValidator:
    """Test input validation and sanitization"""
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        # Normal string
        assert InputValidator.sanitize_string("test") == "test"
        
        # HTML escape
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        
        # Max length
        long_string = "a" * 200
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_validate_api_key(self):
        """Test API key validation"""
        # Valid key
        assert InputValidator.validate_api_key("xai-test-key-12345678901234567890")
        
        # Too short
        assert not InputValidator.validate_api_key("short")
        
        # Contains script tag
        assert not InputValidator.validate_api_key("xai-key-<script>")
        
        # None/empty
        assert not InputValidator.validate_api_key(None)
        assert not InputValidator.validate_api_key("")
    
    def test_validate_tool_name(self):
        """Test tool name validation"""
        # Valid names
        assert InputValidator.validate_tool_name("Salesforce")
        assert InputValidator.validate_tool_name("HubSpot CRM")
        assert InputValidator.validate_tool_name("test-tool_123")
        
        # Invalid names
        assert not InputValidator.validate_tool_name("test<script>")
        assert not InputValidator.validate_tool_name("a" * 200)
        assert not InputValidator.validate_tool_name("")
    
    def test_detect_xss(self):
        """Test XSS detection"""
        assert InputValidator.detect_xss("<script>alert('xss')</script>")
        assert InputValidator.detect_xss("javascript:alert('xss')")
        assert InputValidator.detect_xss("onclick='alert(1)'")
        assert not InputValidator.detect_xss("normal text")
    
    def test_detect_sql_injection(self):
        """Test SQL injection detection"""
        assert InputValidator.detect_sql_injection("'; DROP TABLE users; --")
        assert InputValidator.detect_sql_injection("1' OR '1'='1")
        assert not InputValidator.detect_sql_injection("normal query")


class TestSecurityManager:
    """Test security manager"""
    
    def test_get_api_key_from_env(self, monkeypatch):
        """Test API key retrieval from environment"""
        monkeypatch.setenv("XAI_API_KEY", "test-key-12345678901234567890")
        manager = SecurityManager()
        key = manager.get_api_key(source="env")
        assert key == "test-key-12345678901234567890"
    
    def test_hash_api_key(self):
        """Test API key hashing"""
        manager = SecurityManager()
        key = "test-key"
        hashed = manager.hash_api_key(key)
        assert hashed != key
        assert len(hashed) == 64  # SHA256 hex length
    
    def test_sanitize_user_input(self):
        """Test user input sanitization"""
        manager = SecurityManager()
        
        # String input
        result = manager.sanitize_user_input("test")
        assert result == "test"
        
        # List input
        result = manager.sanitize_user_input(["test1", "test2"])
        assert result == ["test1", "test2"]
        
        # Dict input
        result = manager.sanitize_user_input({"key": "value"})
        assert result == {"key": "value"}
