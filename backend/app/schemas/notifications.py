from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enumeration"""
    TRADE_OPENED = "TRADE_OPENED"
    TRADE_CLOSED = "TRADE_CLOSED"
    TRADE_TRIGGERED = "TRADE_TRIGGERED"
    STRATEGY_EXECUTED = "STRATEGY_EXECUTED"
    STRATEGY_FAILED = "STRATEGY_FAILED"
    PRICE_ALERT = "PRICE_ALERT"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    MARKET_NEWS = "MARKET_NEWS"


class NotificationPriority(str, Enum):
    """Notification priority enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationChannel(str, Enum):
    """Notification channel enumeration"""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"
    SLACK = "SLACK"
    DISCORD = "DISCORD"


class NotificationStatus(str, Enum):
    """Notification status enumeration"""
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"


class NotificationCreateRequest(BaseModel):
    """Request for creating a notification"""
    user_id: Optional[int] = Field(None, description="User ID (null for system notifications)")
    type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=2000, description="Notification message")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Notification priority")
    channel: NotificationChannel = Field(NotificationChannel.IN_APP, description="Delivery channel")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    read: bool = Field(False, description="Whether notification is read")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    
    @validator('title')
    def normalize_title(cls, v):
        return v.strip()
    
    @validator('message')
    def normalize_message(cls, v):
        return v.strip()


class NotificationUpdateRequest(BaseModel):
    """Request for updating a notification"""
    read: Optional[bool] = Field(None, description="Mark as read/unread")
    priority: Optional[NotificationPriority] = Field(None, description="Update priority")
    expires_at: Optional[datetime] = Field(None, description="Update expiration time")


class NotificationResponse(BaseModel):
    """Response model for notification data"""
    id: int
    user_id: Optional[int] = None
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    channel: NotificationChannel
    data: Optional[Dict[str, Any]] = None
    read: bool
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationListRequest(BaseModel):
    """Request for listing notifications with filters"""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    type: Optional[NotificationType] = Field(None, description="Filter by notification type")
    priority: Optional[NotificationPriority] = Field(None, description="Filter by priority")
    channel: Optional[NotificationChannel] = Field(None, description="Filter by channel")
    read: Optional[bool] = Field(None, description="Filter by read status")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")
    expires_before: Optional[datetime] = Field(None, description="Filter expired notifications")
    created_after: Optional[datetime] = Field(None, description="Filter notifications created after date")


class NotificationStatsResponse(BaseModel):
    """Response model for notification statistics"""
    total_notifications: int = Field(..., ge=0, description="Total number of notifications")
    unread_notifications: int = Field(..., ge=0, description="Number of unread notifications")
    read_notifications: int = Field(..., ge=0, description="Number of read notifications")
    pending_notifications: int = Field(..., ge=0, description="Number of pending notifications")
    failed_notifications: int = Field(..., ge=0, description="Number of failed notifications")
    notifications_by_type: Dict[str, int] = Field(default={}, description="Notifications grouped by type")
    notifications_by_priority: Dict[str, int] = Field(default={}, description="Notifications grouped by priority")
    notifications_by_channel: Dict[str, int] = Field(default={}, description="Notifications grouped by channel")
    avg_delivery_time_seconds: Optional[float] = Field(None, description="Average delivery time in seconds")
    delivery_success_rate: Optional[float] = Field(None, description="Delivery success rate percentage")


class NotificationTemplateCreateRequest(BaseModel):
    """Request for creating a notification template"""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    type: NotificationType = Field(..., description="Template type")
    title_template: str = Field(..., min_length=1, max_length=200, description="Title template with placeholders")
    message_template: str = Field(..., min_length=1, max_length=2000, description="Message template with placeholders")
    default_priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Default priority")
    default_channel: NotificationChannel = Field(NotificationChannel.IN_APP, description="Default channel")
    variables: List[str] = Field(default=[], description="Template variables")
    description: Optional[str] = Field("", max_length=500, description="Template description")
    is_active: bool = Field(True, description="Whether template is active")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip().title()


class NotificationTemplateResponse(BaseModel):
    """Response model for notification template data"""
    id: int
    name: str
    type: NotificationType
    title_template: str
    message_template: str
    default_priority: NotificationPriority
    default_channel: NotificationChannel
    variables: List[str]
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationBatchRequest(BaseModel):
    """Request for batch notification operations"""
    notification_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of notification IDs")
    action: str = Field(..., description="Action to perform (mark_read, mark_unread, delete)")


class NotificationSendRequest(BaseModel):
    """Request for sending notifications to multiple users"""
    template_id: Optional[int] = Field(None, description="Template ID to use")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=2000, description="Notification message")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Notification priority")
    channel: NotificationChannel = Field(NotificationChannel.IN_APP, description="Delivery channel")
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="List of user IDs")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule notification for future delivery")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class NotificationSettingsRequest(BaseModel):
    """Request for updating user notification settings"""
    user_id: int = Field(..., description="User ID")
    enabled_channels: List[NotificationChannel] = Field(default=[], description="Enabled notification channels")
    quiet_hours: Dict[str, str] = Field(default={}, description="Quiet hours by day")
    min_priority: NotificationPriority = Field(NotificationPriority.LOW, description="Minimum priority to notify")
    email_address: Optional[str] = Field(None, description="Email address for notifications")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    slack_webhook: Optional[str] = Field(None, description="Slack webhook URL")
    discord_webhook: Optional[str] = Field(None, description="Discord webhook URL")


class NotificationSettingsResponse(BaseModel):
    """Response model for user notification settings"""
    user_id: int
    enabled_channels: List[NotificationChannel]
    quiet_hours: Dict[str, str]
    min_priority: NotificationPriority
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    webhook_url: Optional[str] = None
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationDigestRequest(BaseModel):
    """Request for notification digest"""
    user_id: int = Field(..., description="User ID")
    frequency: str = Field("daily", description="Digest frequency (hourly, daily, weekly)")
    types: Optional[List[NotificationType]] = Field(None, description="Notification types to include")
    include_read: bool = Field(False, description="Include already read notifications")
    max_items: int = Field(50, ge=1, le=200, description="Maximum items per digest")


class NotificationDigestResponse(BaseModel):
    """Response model for notification digest"""
    digest_id: int
    user_id: int
    frequency: str
    generated_at: datetime
    total_notifications: int
    notifications: List[NotificationResponse]
    next_digest_at: datetime
