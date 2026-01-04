"""Custom Notification Rule schemas"""
from pydantic import BaseModel
from datetime import datetime, time
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal


class CustomNotificationRuleCreate(BaseModel):
    """Schema for creating a custom notification rule"""
    rule_name: str
    rule_type: str  # price_alert, indicator, news, pattern
    indicator_type: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    frequency: str = "immediate"  # immediate, daily, weekly
    urgency_level: str = "normal"  # low, normal, high, critical
    is_enabled: bool = True
    sensitivity: Decimal = Decimal("5.0")
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    notify_email: bool = True
    notify_push: bool = False
    notify_sms: bool = False


class CustomNotificationRuleUpdate(BaseModel):
    """Schema for updating a rule"""
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    indicator_type: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    frequency: Optional[str] = None
    urgency_level: Optional[str] = None
    is_enabled: Optional[bool] = None
    sensitivity: Optional[Decimal] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    notify_email: Optional[bool] = None
    notify_push: Optional[bool] = None
    notify_sms: Optional[bool] = None


class CustomNotificationRuleResponse(BaseModel):
    """Schema for rule response"""
    id: UUID
    user_id: UUID
    rule_name: str
    rule_type: str
    indicator_type: Optional[str]
    conditions: Dict[str, Any]
    frequency: str
    urgency_level: str
    is_enabled: bool
    sensitivity: Decimal
    quiet_hours_start: Optional[time]
    quiet_hours_end: Optional[time]
    notify_email: bool
    notify_push: bool
    notify_sms: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
