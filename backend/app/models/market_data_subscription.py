"""Market Data Subscription model"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Uuid, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base


class MarketDataSubscription(Base):
    """Market data subscription model"""
    __tablename__ = 'market_data_subscriptions'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False)  # polygon, alpaca, yfinance
    is_active = Column(Boolean, default=True)
    
    # Provider-specific configuration
    config = Column(JSON, nullable=True)   # api_key, free, oauth
    
    # Encrypted credentials (use Fernet encryption)
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)
    
    features = Column(JSON, default=list)  # List of enabled features
    
    # is_active defined above
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<MarketDataSubscription(user_id={self.user_id}, provider={self.provider})>"
