"""Notification Settings schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class NotificationSettingsUpdate(BaseModel):
    """Schema for updating notification settings"""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    price_alerts: Optional[bool] = None
    goal_progress_alerts: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    daily_summary: Optional[bool] = None


class NotificationSettingsResponse(BaseModel):
    """Schema for notification settings response"""
    id: UUID
    user_id: UUID
    email_notifications: bool
    push_notifications: bool
    price_alerts: bool
    goal_progress_alerts: bool
    weekly_reports: bool
    daily_summary: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
