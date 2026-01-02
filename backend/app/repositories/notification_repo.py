from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

from app.schemas.notifications import (
    NotificationCreateRequest, NotificationUpdateRequest, NotificationType,
    NotificationPriority, NotificationChannel, NotificationStatus,
    NotificationListRequest, NotificationTemplateCreateRequest,
    NotificationBatchRequest, NotificationSendRequest,
    NotificationSettingsRequest, NotificationDigestRequest
)


class NotificationRepository(Protocol):
    """Repository interface for notification operations"""
    
    async def create_notification(self, notification_data: NotificationCreateRequest) -> int:
        """Create a new notification and return its ID"""
        ...
    
    async def get_notification_by_id(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get a single notification by ID"""
        ...
    
    async def get_all_notifications(
        self,
        user_id: Optional[int] = None,
        type: Optional[NotificationType] = None,
        priority: Optional[NotificationPriority] = None,
        channel: Optional[NotificationChannel] = None,
        read: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        expires_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get all notifications with optional filters"""
        ...
    
    async def update_notification(self, notification_id: int, updates: NotificationUpdateRequest) -> bool:
        """Update a notification"""
        ...
    
    async def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        ...
    
    async def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read"""
        ...
    
    async def mark_notifications_read(self, notification_ids: List[int]) -> int:
        """Mark multiple notifications as read"""
        ...
    
    async def mark_all_read(self, user_id: Optional[int] = None) -> int:
        """Mark all notifications as read for a user or all users"""
        ...
    
    async def get_unread_count(self, user_id: Optional[int] = None) -> int:
        """Get count of unread notifications for a user or all users"""
        ...
    
    async def get_notification_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregate notification statistics"""
        ...
    
    async def search_notifications(self, query: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search notifications by title or message"""
        ...
    
    async def batch_update_notifications(self, notification_ids: List[int], updates: Dict[str, Any]) -> int:
        """Update multiple notifications at once"""
        ...
    
    async def batch_delete_notifications(self, notification_ids: List[int]) -> int:
        """Delete multiple notifications at once"""
        ...
    
    async def cleanup_expired_notifications(self) -> int:
        """Delete expired notifications"""
        ...


class NotificationTemplateRepository(Protocol):
    """Repository interface for notification template operations"""
    
    async def create_template(self, template_data: NotificationTemplateCreateRequest) -> int:
        """Create a new notification template and return its ID"""
        ...
    
    async def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a single template by ID"""
        ...
    
    async def get_all_templates(
        self,
        type: Optional[NotificationType] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all templates with optional filters"""
        ...
    
    async def update_template(self, template_id: int, updates: Dict[str, Any]) -> bool:
        """Update a template"""
        ...
    
    async def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        ...
    
    async def get_active_templates(self) -> List[Dict[str, Any]]:
        """Get all active templates"""
        ...
    
    async def render_template(self, template_id: int, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Render a template with provided variables"""
        ...


class NotificationSettingsRepository(Protocol):
    """Repository interface for user notification settings"""
    
    async def get_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get notification settings for a user"""
        ...
    
    async def update_settings(self, user_id: int, settings: NotificationSettingsRequest) -> bool:
        """Update notification settings for a user"""
        ...
    
    async def create_settings(self, settings: NotificationSettingsRequest) -> int:
        """Create notification settings for a user"""
        ...
    
    async def get_users_with_enabled_channel(self, channel: NotificationChannel) -> List[int]:
        """Get all users who have enabled a specific channel"""
        ...


class NotificationDeliveryRepository(Protocol):
    """Repository interface for notification delivery operations"""
    
    async def send_notification(self, notification_data: NotificationCreateRequest) -> Dict[str, Any]:
        """Send a single notification"""
        ...
    
    async def send_bulk_notifications(self, request: NotificationSendRequest) -> Dict[str, Any]:
        """Send notifications to multiple users"""
        ...
    
    async def get_delivery_status(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get delivery status for a notification"""
        ...
    
    async def retry_failed_notifications(self, max_retries: int = 3) -> int:
        """Retry failed notifications"""
        ...
    
    async def get_delivery_stats(self, channel: Optional[NotificationChannel] = None) -> Dict[str, Any]:
        """Get delivery statistics by channel"""
        ...


class NotificationDigestRepository(Protocol):
    """Repository interface for notification digest operations"""
    
    async def create_digest(self, request: NotificationDigestRequest) -> int:
        """Create a notification digest"""
        ...
    
    async def get_digests(self, user_id: int, frequency: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get digests for a user"""
        ...
    
    async def get_latest_digest(self, user_id: int, frequency: str) -> Optional[Dict[str, Any]]:
        """Get latest digest for a user and frequency"""
        ...
    
    async def mark_digest_sent(self, digest_id: int) -> bool:
        """Mark digest as sent"""
        ...
