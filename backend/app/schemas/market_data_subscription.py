"""Market Data Subscription schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class MarketDataProviderInfo(BaseModel):
    """Information about an available market data provider"""
    id: str
    name: str
    type: str  # api_key, free, oauth
    description: str
    supports_realtime: bool
    requires_api_key: bool


class MarketDataSubscriptionCreate(BaseModel):
    """Schema for creating a subscription"""
    provider_name: str
    provider_type: str
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    subscription_tier: Optional[str] = None
    features: Optional[List[str]] = None


class MarketDataSubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    subscription_tier: Optional[str] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


class MarketDataSubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: UUID
    user_id: UUID
    provider_name: str
    provider_type: str
    subscription_tier: Optional[str] = None
    features: List[str] = []
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Note: We don't return encrypted credentials for security
    
    class Config:
        from_attributes = True
