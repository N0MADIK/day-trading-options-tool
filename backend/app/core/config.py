from pydantic import Field
from typing import Optional
import os


class Settings:
    """Application settings with environment variable support"""
    
    def __init__(self):
        # Application
        self.app_name = "Options Trading API"
        self.app_version = "1.0.0"
        self.debug = False
        
        # Database
        self.database_url = "sqlite+aiosqlite:///./data/trading.db"
        
        # API
        self.api_v1_prefix = "/api/v1"
        
        # CORS
        self.cors_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173", 
            "http://localhost",
            "http://localhost:80",
            "http://localhost:8420"
        ]
        
        # External Services
        self.yfinance_timeout = 30
        self.google_ai_timeout = 30
        
        # Background Jobs
        self.scheduler_enabled = True
        
        # Security
        self.secret_key = "your-secret-key-change-in-production"
        self.credential_encryption_key = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
        
        # JWT Settings
        self.jwt_secret_key = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_minutes = int(os.getenv('JWT_EXPIRATION_MINUTES', '60'))
        
        # External Service APIs
        # Plaid
        self.plaid_client_id = os.getenv('PLAID_CLIENT_ID')
        self.plaid_secret = os.getenv('PLAID_SECRET')
        self.plaid_base_url = os.getenv('PLAID_BASE_URL', 'https://development.plaid.com')
        
        # Alpaca
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        # SnapTrade
        self.snaptrade_client_id = os.getenv('SNAPTRADE_CLIENT_ID')
        self.snaptrade_consumer_key = os.getenv('SNAPTRADE_CONSUMER_KEY')


# Global settings instance
settings = Settings()
