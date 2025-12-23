"""
Encryption Utilities for Finance Module

Provides secure encryption/decryption for auth tokens and sensitive data.
Uses Fernet symmetric encryption with a key from environment variables.
"""
import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet


def get_encryption_key() -> bytes:
    """
    Get or generate the encryption key.
    In production, this should come from a secure key management system.
    """
    key_str = os.environ.get("FINANCE_ENCRYPTION_KEY")
    
    if key_str:
        # Use provided key (should be 32 bytes, base64 encoded = 44 chars)
        if len(key_str) == 44:
            return key_str.encode()
        else:
            # Derive a key from the provided string
            derived = hashlib.sha256(key_str.encode()).digest()
            return base64.urlsafe_b64encode(derived)
    else:
        # Generate a dev key based on a fixed seed (NOT for production!)
        # This ensures the same key is used across restarts in development
        dev_seed = "dev_finance_key_change_in_production"
        derived = hashlib.sha256(dev_seed.encode()).digest()
        return base64.urlsafe_b64encode(derived)


def encrypt_auth_blob(data: str) -> str:
    """
    Encrypt sensitive auth data (tokens, credentials).
    
    Args:
        data: Plain text data to encrypt
        
    Returns:
        Base64-encoded encrypted string
    """
    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_auth_blob(encrypted_data: str) -> Optional[str]:
    """
    Decrypt auth data.
    
    Args:
        encrypted_data: Base64-encoded encrypted string
        
    Returns:
        Decrypted plain text, or None if decryption fails
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None


def generate_new_key() -> str:
    """
    Generate a new Fernet key.
    Use this to create a new FINANCE_ENCRYPTION_KEY for production.
    
    Returns:
        Base64-encoded key string (44 characters)
    """
    key = Fernet.generate_key()
    return key.decode()


# Test function
if __name__ == "__main__":
    # Generate a new key
    print("New encryption key:", generate_new_key())
    
    # Test encrypt/decrypt
    test_data = '{"access_token": "secret123", "refresh_token": "refresh456"}'
    encrypted = encrypt_auth_blob(test_data)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = decrypt_auth_blob(encrypted)
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_data == decrypted}")
