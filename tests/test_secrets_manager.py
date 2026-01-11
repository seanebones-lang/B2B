"""Tests for secrets manager"""

import pytest
import os
from unittest.mock import patch

from utils.secrets_manager import SecretsManager, get_secrets_manager


class TestSecretsManager:
    """Test secrets manager functionality"""
    
    def test_init_without_key(self):
        """Test initialization without master key"""
        manager = SecretsManager()
        assert manager.cipher_suite is None
    
    def test_init_with_key(self):
        """Test initialization with master key"""
        manager = SecretsManager(master_key="test_key_12345")
        assert manager.cipher_suite is not None
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        manager = SecretsManager(master_key="test_key_12345")
        
        plaintext = "sensitive_data"
        encrypted = manager.encrypt(plaintext)
        
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        
        decrypted = manager.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_without_cipher(self):
        """Test encryption without cipher suite"""
        manager = SecretsManager()
        plaintext = "test"
        result = manager.encrypt(plaintext)
        assert result == plaintext
    
    def test_decrypt_without_cipher(self):
        """Test decryption without cipher suite"""
        manager = SecretsManager()
        ciphertext = "test"
        result = manager.decrypt(ciphertext)
        assert result == ciphertext
    
    def test_get_secret_from_env(self):
        """Test getting secret from environment"""
        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            manager = SecretsManager()
            value = manager.get_secret("TEST_SECRET")
            assert value == "test_value"
    
    def test_get_secret_encrypted(self):
        """Test getting encrypted secret"""
        manager = SecretsManager(master_key="test_key_12345")
        encrypted = manager.encrypt("secret_value")
        
        with patch.dict(os.environ, {"TEST_SECRET": encrypted}):
            value = manager.get_secret("TEST_SECRET", encrypted=True)
            assert value == "secret_value"
    
    def test_set_secret(self):
        """Test setting secret"""
        manager = SecretsManager(master_key="test_key_12345")
        encrypted = manager.set_secret("TEST_KEY", "secret_value", encrypt=True)
        
        assert encrypted != "secret_value"
        assert isinstance(encrypted, str)
        
        # Verify it can be decrypted
        decrypted = manager.decrypt(encrypted)
        assert decrypted == "secret_value"
    
    def test_get_secrets_manager_singleton(self):
        """Test singleton pattern"""
        manager1 = get_secrets_manager()
        manager2 = get_secrets_manager()
        assert manager1 is manager2
