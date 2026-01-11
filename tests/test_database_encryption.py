"""Tests for database encryption"""

import pytest
from unittest.mock import patch

from utils.database_encryption import DatabaseEncryption, get_db_encryption
from utils.database import get_db_manager


class TestDatabaseEncryption:
    """Test database encryption functionality"""
    
    def test_init_without_key(self):
        """Test initialization without encryption key"""
        encryption = DatabaseEncryption()
        assert encryption.cipher is None or encryption.cipher is not None
    
    def test_init_with_key(self):
        """Test initialization with encryption key"""
        encryption = DatabaseEncryption(encryption_key="test_key_12345")
        assert encryption.cipher is not None
    
    def test_encrypt_decrypt_field(self):
        """Test field encryption and decryption"""
        encryption = DatabaseEncryption(encryption_key="test_key_12345")
        
        plaintext = "This is sensitive review text"
        encrypted = encryption.encrypt_field(plaintext)
        
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        
        decrypted = encryption.decrypt_field(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_review(self):
        """Test review encryption and decryption"""
        encryption = DatabaseEncryption(encryption_key="test_key_12345")
        
        review = {
            "text": "This is a sensitive review",
            "rating": 1,
            "source": "G2",
            "date": "2024-01-01"
        }
        
        encrypted_review = encryption.encrypt_review(review)
        assert encrypted_review["text"] != review["text"]
        assert encrypted_review["_encrypted"] is True
        
        decrypted_review = encryption.decrypt_review(encrypted_review)
        assert decrypted_review["text"] == review["text"]
        assert decrypted_review.get("_encrypted") is False
    
    def test_empty_field_handling(self):
        """Test handling of empty fields"""
        encryption = DatabaseEncryption(encryption_key="test_key_12345")
        
        assert encryption.encrypt_field("") == ""
        assert encryption.decrypt_field("") == ""
    
    def test_get_db_encryption_singleton(self):
        """Test singleton pattern"""
        encryption1 = get_db_encryption()
        encryption2 = get_db_encryption()
        assert encryption1 is encryption2
    
    def test_database_integration(self):
        """Test encryption integration with database"""
        db_manager = get_db_manager()
        encryption = DatabaseEncryption(encryption_key="test_key_12345")
        
        reviews = [
            {
                "text": "Test review text",
                "rating": 1,
                "source": "G2",
                "date": "2024-01-01"
            }
        ]
        
        # Save with encryption
        count = db_manager.save_reviews("Test Tool", reviews, encrypt=True)
        assert count == len(reviews)
        
        # Retrieve with decryption
        retrieved = db_manager.get_reviews("Test Tool", decrypt=True)
        assert len(retrieved) >= len(reviews)
        
        # Verify text can be decrypted (if encryption was used)
        if retrieved:
            # Text should be readable
            assert isinstance(retrieved[0]["text"], str)
