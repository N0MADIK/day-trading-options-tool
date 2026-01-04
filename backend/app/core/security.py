"""Security utilities for encryption and authentication"""
from cryptography.fernet import Fernet
from typing import Dict, Any
import json
import os
from passlib.context import CryptContext
import secrets


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CredentialEncryption:
    """Handle encryption/decryption of sensitive credentials"""
    
    def __init__(self):
        # Get or generate encryption key
        encryption_key = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
        if not encryption_key:
            # Generate a new key if not provided (for development)
            encryption_key = Fernet.generate_key().decode()
            print(f"WARNING: Generated new encryption key. Set CREDENTIAL_ENCRYPTION_KEY={encryption_key}")
        
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary to string"""
        json_str = json.dumps(credentials)
        encrypted = self.fernet.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt credentials string to dictionary"""
        decrypted = self.fernet.decrypt(encrypted_credentials.encode())
        return json.loads(decrypted.decode())
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a single value"""
        encrypted = self.fernet.encrypt(value.encode())
        return encrypted.decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a single value"""
        decrypted = self.fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def generate_secret_key() -> str:
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)


# Global instance
credential_encryption = CredentialEncryption()
