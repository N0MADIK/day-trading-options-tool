"""Net Worth schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal


class NetWorthSnapshotCreate(BaseModel):
    """Schema for creating a net worth snapshot"""
    total_net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Optional[Decimal] = 0
    breakdown: Optional[Dict[str, Any]] = None


class NetWorthHistoryResponse(BaseModel):
    """Schema for net worth history response"""
    id: UUID
    user_id: UUID
    total_net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    breakdown: Dict[str, Any] = {}
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class NetWorthSummary(BaseModel):
    """Schema for current net worth summary"""
    total_net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    change_today: Decimal
    change_percent: float
    last_updated: Optional[datetime]


class NetWorthGoalCreate(BaseModel):
    """Schema for creating/updating a goal"""
    target_amount: Decimal
    target_date: Optional[datetime] = None
    notify_on_progress: bool = True
    notify_threshold_percent: Decimal = Decimal("5.00")


class NetWorthGoalUpdate(BaseModel):
    """Schema for updating a goal"""
    target_amount: Optional[Decimal] = None
    target_date: Optional[datetime] = None
    notify_on_progress: Optional[bool] = None
    notify_threshold_percent: Optional[Decimal] = None


class NetWorthGoalResponse(BaseModel):
    """Schema for goal response"""
    id: UUID
    user_id: UUID
    target_amount: Decimal
    target_date: Optional[datetime]
    notify_on_progress: bool
    notify_threshold_percent: Decimal
    last_notified_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
