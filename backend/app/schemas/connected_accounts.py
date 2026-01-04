"""Connected Accounts schemas for finance-flow compatibility"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class ConnectedAccountBase(BaseModel):
    """Base schema for connected accounts"""
    institution_name: str
    institution_type: str  # bank, brokerage, credit_card, etc.
    account_name: str
    account_number_masked: Optional[str] = None


class ConnectedAccountCreate(ConnectedAccountBase):
    """Schema for creating a connected account"""
    plaid_item_id: Optional[str] = None
    snaptrade_authorization_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConnectedAccountUpdate(BaseModel):
    """Schema for updating a connected account"""
    account_name: Optional[str] = None
    is_connected: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ConnectedAccountResponse(ConnectedAccountBase):
    """Schema for connected account response - matches finance-flow frontend expectations"""
    id: UUID
    user_id: UUID
    balance: float = 0.0
    is_connected: bool = True
    connection_status: str = "active"  # active, needs_reauth, error, disabled
    last_synced_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConnectedAccountSync(BaseModel):
    """Schema for sync status response"""
    account_id: UUID
    status: str  # pending, syncing, completed, failed
    message: Optional[str] = None
    last_synced_at: Optional[datetime] = None
