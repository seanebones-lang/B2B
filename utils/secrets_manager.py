"""Secrets management with encryption support"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from utils.logging import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """Secrets management with encryption at rest"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize secrets manager
        
        Args:
            master_key: Master encryption key (defaults to SECRET_KEY env var)
        """
        self.master_key = master_key or os.getenv("SECRET_KEY")
        self.cipher_suite = None
        
        if self.master_key:
            try:
                self.cipher_suite = self._create_cipher_suite(self.master_key)
                logger.info("Secrets manager initialized with encryption")
            except Exception as e:
                logger.warning("Failed to initialize encryption", error=str(e))
                self.cipher_suite = None
        else:
            logger.warning("No SECRET_KEY found, secrets will not be encrypted")
    
    def _create_cipher_suite(self, password: str) -> Fernet:
        """
        Create Fernet cipher suite from password
        
        Args:
            password: Master password
            
        Returns:
            Fernet cipher suite
        """
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'fixed_salt_for_key_derivation',  # In production, use random salt stored securely
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext
        
        Args:
            plaintext: Text to encrypt
            
        Returns:
            Encrypted text (base64 encoded)
        """
        if not self.cipher_suite:
            logger.warning("Encryption not available, returning plaintext")
            return plaintext
        
        try:
            encrypted = self.cipher_suite.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext
        
        Args:
            ciphertext: Encrypted text (base64 encoded)
            
        Returns:
            Decrypted plaintext
        """
        if not self.cipher_suite:
            logger.warning("Decryption not available, returning as-is")
            return ciphertext
        
        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self.cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise
    
    def get_secret(self, key: str, encrypted: bool = False) -> Optional[str]:
        """
        Get secret from environment or encrypted storage
        
        Args:
            key: Secret key name
            encrypted: Whether the stored value is encrypted
            
        Returns:
            Secret value or None
        """
        value = os.getenv(key)
        
        if value and encrypted and self.cipher_suite:
            try:
                return self.decrypt(value)
            except Exception as e:
                logger.error("Failed to decrypt secret", key=key, error=str(e))
                return None
        
        return value
    
    def set_secret(self, key: str, value: str, encrypt: bool = True) -> str:
        """
        Encrypt and prepare secret for storage
        
        Args:
            key: Secret key name
            value: Secret value
            encrypt: Whether to encrypt the value
            
        Returns:
            Encrypted value (if encrypt=True) or plain value
        """
        if encrypt and self.cipher_suite:
            try:
                return self.encrypt(value)
            except Exception as e:
                logger.error("Failed to encrypt secret", key=key, error=str(e))
                return value
        
        return value


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
