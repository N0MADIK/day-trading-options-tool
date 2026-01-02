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


# Global settings instance
settings = Settings()
