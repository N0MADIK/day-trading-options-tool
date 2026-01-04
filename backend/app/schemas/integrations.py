"""Schemas for integration API endpoints"""
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class IntegrationTypeEnum(str, Enum):
    """Integration types"""
    PLAID = "plaid"
    ALPACA = "alpaca"
    SNAPTRADE = "snaptrade"


class IntegrationStatusEnum(str, Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    EXPIRED = "expired"


# Plaid schemas
class PlaidCredentials(BaseModel):
    """Plaid credentials"""
    access_token: Optional[str] = None
    public_token: Optional[str] = None
    
    @validator('*', pre=True)
    def at_least_one_token(cls, v, values):
        if not v and not any(values.values()):
            raise ValueError('Either access_token or public_token must be provided')
        return v


class PlaidLinkTokenRequest(BaseModel):
    """Request to create Plaid Link token"""
    user_id: str
    webhook_url: Optional[str] = None


# Alpaca schemas
class AlpacaCredentials(BaseModel):
    """Alpaca API credentials"""
    api_key: str
    secret_key: str
    is_paper_trading: bool = True


# SnapTrade schemas
class SnapTradeCredentials(BaseModel):
    """SnapTrade credentials"""
    user_secret: Optional[str] = None
    user_id: Optional[str] = None


class SnapTradeRegisterRequest(BaseModel):
    """Request to register SnapTrade user"""
    user_id: str


class SnapTradeConnectionRequest(BaseModel):
    """Request to initiate SnapTrade brokerage connection"""
    brokerage_id: str
    redirect_uri: str


# General integration schemas
class CreateIntegrationRequest(BaseModel):
    """Request to create a new integration"""
    integration_type: IntegrationTypeEnum
    credentials: Dict[str, Any]
    is_sandbox: bool = True
    
    @validator('credentials')
    def validate_credentials(cls, v, values):
        integration_type = values.get('integration_type')
        
        if integration_type == IntegrationTypeEnum.PLAID:
            PlaidCredentials(**v)
        elif integration_type == IntegrationTypeEnum.ALPACA:
            AlpacaCredentials(**v)
        elif integration_type == IntegrationTypeEnum.SNAPTRADE:
            SnapTradeCredentials(**v)
        
        return v


class UpdateCredentialsRequest(BaseModel):
    """Request to update integration credentials"""
    credentials: Dict[str, Any]


class IntegrationResponse(BaseModel):
    """Integration response"""
    id: int
    integration_type: str
    status: str
    is_sandbox: bool
    last_sync_at: Optional[str] = None
    created_at: Optional[str] = None
    connected_accounts: int = 0


class TestConnectionResponse(BaseModel):
    """Test connection response"""
    connected: bool
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SyncAccountsResponse(BaseModel):
    """Sync accounts response"""
    synced_accounts: List[Dict[str, Any]]
    total: int


class ConnectedAccountResponse(BaseModel):
    """Connected account response"""
    id: int
    external_account_id: str
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    account_subtype: Optional[str] = None
    institution_name: Optional[str] = None
    is_active: bool
    sync_enabled: bool
    last_successful_sync: Optional[str] = None
