"""Database field encryption utilities"""

import secrets
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
import os

from utils.secrets_manager import get_secrets_manager
from utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseEncryption:
    """Encryption utilities for database fields"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize database encryption
        
        Args:
            encryption_key: Encryption key (defaults to SECRET_KEY env var)
        """
        secrets_manager = get_secrets_manager()
        
        if encryption_key:
            # Derive Fernet key from password using secure salt
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            
            # Get salt from environment or generate a secure one
            salt_env = os.getenv("DB_ENCRYPTION_SALT")
            if salt_env:
                try:
                    salt = base64.urlsafe_b64decode(salt_env.encode())
                except Exception:
                    logger.warning("Invalid salt in DB_ENCRYPTION_SALT, generating new one")
                    salt = secrets.token_bytes(16)
            else:
                salt = secrets.token_bytes(16)
                logger.warning(
                    "No DB_ENCRYPTION_SALT found, using random salt. "
                    "For production, set DB_ENCRYPTION_SALT environment variable with a base64-encoded 16-byte salt."
                )
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            self.cipher = Fernet(key)
        else:
            # Try to get from secrets manager
            key = os.getenv("DB_ENCRYPTION_KEY") or os.getenv("SECRET_KEY")
            if key:
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                from cryptography.hazmat.backends import default_backend
                
                # Get salt from environment or generate a secure one
                salt_env = os.getenv("DB_ENCRYPTION_SALT")
                if salt_env:
                    try:
                        salt = base64.urlsafe_b64decode(salt_env.encode())
                    except Exception:
                        logger.warning("Invalid salt in DB_ENCRYPTION_SALT, generating new one")
                        salt = secrets.token_bytes(16)
                else:
                    salt = secrets.token_bytes(16)
                    logger.warning(
                        "No DB_ENCRYPTION_SALT found, using random salt. "
                        "For production, set DB_ENCRYPTION_SALT environment variable with a base64-encoded 16-byte salt."
                    )
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
                self.cipher = Fernet(key_bytes)
            else:
                logger.warning("No encryption key found, database encryption disabled")
                self.cipher = None
    
    def encrypt_field(self, value: str) -> str:
        """
        Encrypt a database field value
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value (base64 encoded)
        """
        if not self.cipher:
            logger.warning("Encryption not available, returning plaintext")
            return value
        
        if not value:
            return value
        
        try:
            encrypted = self.cipher.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error("Field encryption failed", error=str(e))
            raise
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """
        Decrypt a database field value
        
        Args:
            encrypted_value: Encrypted value (base64 encoded)
            
        Returns:
            Decrypted plaintext
        """
        if not self.cipher:
            logger.warning("Decryption not available, returning as-is")
            return encrypted_value
        
        if not encrypted_value:
            return encrypted_value
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error("Field decryption failed", error=str(e))
            # Return as-is if decryption fails (might be plaintext)
            return encrypted_value
    
    def encrypt_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a review
        
        Args:
            review: Review dictionary
            
        Returns:
            Review dictionary with encrypted fields
        """
        encrypted_review = review.copy()
        
        # Encrypt review text (sensitive data)
        if "text" in encrypted_review and encrypted_review["text"]:
            encrypted_review["text"] = self.encrypt_field(encrypted_review["text"])
            encrypted_review["_encrypted"] = True
        
        return encrypted_review
    
    def decrypt_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in a review
        
        Args:
            review: Review dictionary (may contain encrypted fields)
            
        Returns:
            Review dictionary with decrypted fields
        """
        decrypted_review = review.copy()
        
        # Decrypt if encrypted
        if review.get("_encrypted") and "text" in decrypted_review:
            decrypted_review["text"] = self.decrypt_field(decrypted_review["text"])
            decrypted_review["_encrypted"] = False
        
        return decrypted_review


# Global encryption instance
_db_encryption: Optional[DatabaseEncryption] = None


def get_db_encryption() -> DatabaseEncryption:
    """Get global database encryption instance"""
    global _db_encryption
    if _db_encryption is None:
        _db_encryption = DatabaseEncryption()
    return _db_encryption
