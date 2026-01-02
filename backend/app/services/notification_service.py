from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from app.repositories.notification_repo import (
    NotificationRepository, NotificationTemplateRepository,
    NotificationSettingsRepository, NotificationDeliveryRepository,
    NotificationDigestRepository
)
from app.schemas.notifications import (
    NotificationCreateRequest, NotificationUpdateRequest, NotificationType,
    NotificationPriority, NotificationChannel, NotificationStatus,
    NotificationListRequest, NotificationTemplateCreateRequest,
    NotificationBatchRequest, NotificationSendRequest,
    NotificationSettingsRequest, NotificationDigestRequest
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class NotificationService:
    """Service for notification management operations"""
    
    def __init__(
        self,
        notification_repo: NotificationRepository,
        template_repo: NotificationTemplateRepository,
        settings_repo: NotificationSettingsRepository,
        delivery_repo: NotificationDeliveryRepository,
        digest_repo: NotificationDigestRepository
    ):
        self.notification_repo = notification_repo
        self.template_repo = template_repo
        self.settings_repo = settings_repo
        self.delivery_repo = delivery_repo
        self.digest_repo = digest_repo
    
    async def create_notification(self, notification_data: NotificationCreateRequest) -> Dict[str, Any]:
        """Create a new notification"""
        try:
            notification_id = await self.notification_repo.create_notification(notification_data)
            
            # Get created notification
            notification = await self.notification_repo.get_notification_by_id(notification_id)
            
            # Send notification asynchronously
            asyncio.create_task(self._send_notification_async(notification))
            
            return {
                "success": True,
                "notification_id": notification_id,
                "notification": notification
            }
            
        except Exception as e:
            raise e
    
    async def get_notification_by_id(self, notification_id: int) -> Dict[str, Any]:
        """Get a single notification by ID"""
        notification = await self.notification_repo.get_notification_by_id(notification_id)
        
        if not notification:
            raise NotFoundError(f"Notification with ID {notification_id} not found")
        
        return notification
    
    async def list_notifications(self, request: NotificationListRequest) -> List[Dict[str, Any]]:
        """List notifications with optional filters"""
        try:
            notifications = await self.notification_repo.get_all_notifications(
                user_id=request.user_id,
                type=request.type,
                priority=request.priority,
                channel=request.channel,
                read=request.read,
                limit=request.limit,
                offset=request.offset,
                expires_before=request.expires_before,
                created_after=request.created_after
            )
            
            return notifications
            
        except Exception as e:
            raise e
    
    async def update_notification(self, notification_id: int, updates: NotificationUpdateRequest) -> Dict[str, Any]:
        """Update a notification"""
        try:
            success = await self.notification_repo.update_notification(notification_id, updates)
            
            if not success:
                raise NotFoundError(f"Notification with ID {notification_id} not found")
            
            # Return updated notification
            updated_notification = await self.notification_repo.get_notification_by_id(notification_id)
            
            return {
                "success": True,
                "notification": updated_notification
            }
            
        except Exception as e:
            raise e
    
    async def delete_notification(self, notification_id: int) -> Dict[str, Any]:
        """Delete a notification"""
        try:
            success = await self.notification_repo.delete_notification(notification_id)
            
            if not success:
                raise NotFoundError(f"Notification with ID {notification_id} not found")
            
            return {
                "success": True,
                "message": f"Notification {notification_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def mark_notification_read(self, notification_id: int) -> Dict[str, Any]:
        """Mark a notification as read"""
        try:
            success = await self.notification_repo.mark_notification_read(notification_id)
            
            if not success:
                raise NotFoundError(f"Notification with ID {notification_id} not found")
            
            return {
                "success": True,
                "message": f"Notification {notification_id} marked as read"
            }
            
        except Exception as e:
            raise e
    
    async def mark_notifications_read(self, notification_ids: List[int]) -> Dict[str, Any]:
        """Mark multiple notifications as read"""
        try:
            count = await self.notification_repo.mark_notifications_read(notification_ids)
            
            return {
                "success": True,
                "marked_count": count,
                "message": f"Marked {count} notifications as read"
            }
            
        except Exception as e:
            raise e
    
    async def mark_all_read(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Mark all notifications as read for a user or all users"""
        try:
            count = await self.notification_repo.mark_all_read(user_id)
            
            return {
                "success": True,
                "marked_count": count,
                "message": f"Marked {count} notifications as read"
            }
            
        except Exception as e:
            raise e
    
    async def get_unread_count(self, user_id: Optional[int] = None) -> int:
        """Get count of unread notifications for a user or all users"""
        try:
            return await self.notification_repo.get_unread_count(user_id)
        except Exception as e:
            raise e
    
    async def get_notification_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregate notification statistics"""
        try:
            return await self.notification_repo.get_notification_stats(user_id)
        except Exception as e:
            raise e
    
    async def search_notifications(self, query: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search notifications by title or message"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            return await self.notification_repo.search_notifications(query.strip(), user_id)
        except Exception as e:
            raise e
    
    async def batch_update_notifications(self, request: NotificationBatchRequest) -> Dict[str, Any]:
        """Update multiple notifications at once"""
        try:
            # Validate action
            if request.action not in ["mark_read", "mark_unread", "delete"]:
                raise ValidationError("Invalid batch action")
            
            if request.action == "mark_read":
                updates = {"read": True}
                count = await self.notification_repo.batch_update_notifications(
                    request.notification_ids, updates
                )
                message = f"Marked {count} notifications as read"
            elif request.action == "mark_unread":
                updates = {"read": False}
                count = await self.notification_repo.batch_update_notifications(
                    request.notification_ids, updates
                )
                message = f"Marked {count} notifications as unread"
            elif request.action == "delete":
                count = await self.notification_repo.batch_delete_notifications(request.notification_ids)
                message = f"Deleted {count} notifications"
            
            return {
                "success": True,
                "updated_count": count,
                "message": message
            }
            
        except Exception as e:
            raise e
    
    async def cleanup_expired_notifications(self) -> Dict[str, Any]:
        """Delete expired notifications"""
        try:
            count = await self.notification_repo.cleanup_expired_notifications()
            
            return {
                "success": True,
                "deleted_count": count,
                "message": f"Cleaned up {count} expired notifications"
            }
            
        except Exception as e:
            raise e
    
    async def _send_notification_async(self, notification: Dict[str, Any]) -> None:
        """Send notification asynchronously"""
        try:
            # Get user settings to determine delivery channels
            if notification.get('user_id'):
                settings = await self.settings_repo.get_settings(notification['user_id'])
                enabled_channels = settings.get('enabled_channels', [NotificationChannel.IN_APP])
            else:
                enabled_channels = [NotificationChannel.IN_APP]
            
            # Send through enabled channels
            for channel in enabled_channels:
                try:
                    await self.delivery_repo.send_notification(notification)
                except Exception as e:
                    # Log error but continue with other channels
                    print(f"Failed to send notification via {channel}: {e}")
            
            # Update notification status
            await self._update_notification_status(notification['id'], NotificationStatus.SENT)
            
        except Exception as e:
            # Mark as failed
            await self._update_notification_status(notification['id'], NotificationStatus.FAILED)
            print(f"Failed to send notification: {e}")
    
    async def _update_notification_status(self, notification_id: int, status: NotificationStatus) -> None:
        """Update notification status"""
        try:
            updates = {"status": status}
            if status == NotificationStatus.DELIVERED:
                updates["delivered_at"] = datetime.utcnow()
            
            await self.notification_repo.update_notification(notification_id, NotificationUpdateRequest(**updates))
        except Exception:
            pass  # Log error but don't fail the operation


class NotificationTemplateService:
    """Service for notification template management"""
    
    def __init__(self, template_repo: NotificationTemplateRepository):
        self.template_repo = template_repo
    
    async def create_template(self, template_data: NotificationTemplateCreateRequest) -> Dict[str, Any]:
        """Create a new notification template"""
        try:
            template_id = await self.template_repo.create_template(template_data)
            
            # Get created template
            template = await self.template_repo.get_template_by_id(template_id)
            
            return {
                "success": True,
                "template_id": template_id,
                "template": template
            }
            
        except Exception as e:
            raise e
    
    async def get_template_by_id(self, template_id: int) -> Dict[str, Any]:
        """Get a single template by ID"""
        template = await self.template_repo.get_template_by_id(template_id)
        
        if not template:
            raise NotFoundError(f"Template with ID {template_id} not found")
        
        return template
    
    async def list_templates(self, type: Optional[NotificationType] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List templates with optional filters"""
        try:
            return await self.template_repo.get_all_templates(
                type=type,
                is_active=is_active
            )
        except Exception as e:
            raise e
    
    async def update_template(self, template_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a template"""
        try:
            success = await self.template_repo.update_template(template_id, updates)
            
            if not success:
                raise NotFoundError(f"Template with ID {template_id} not found")
            
            # Return updated template
            updated_template = await self.template_repo.get_template_by_id(template_id)
            
            return {
                "success": True,
                "template": updated_template
            }
            
        except Exception as e:
            raise e
    
    async def delete_template(self, template_id: int) -> Dict[str, Any]:
        """Delete a template"""
        try:
            success = await self.template_repo.delete_template(template_id)
            
            if not success:
                raise NotFoundError(f"Template with ID {template_id} not found")
            
            return {
                "success": True,
                "message": f"Template {template_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def get_active_templates(self) -> List[Dict[str, Any]]:
        """Get all active templates"""
        try:
            return await self.template_repo.get_active_templates()
        except Exception as e:
            raise e
    
    async def render_template(self, template_id: int, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Render a template with provided variables"""
        try:
            return await self.template_repo.render_template(template_id, variables)
        except Exception as e:
            raise e


class NotificationSettingsService:
    """Service for user notification settings management"""
    
    def __init__(self, settings_repo: NotificationSettingsRepository):
        self.settings_repo = settings_repo
    
    async def get_settings(self, user_id: int) -> Dict[str, Any]:
        """Get notification settings for a user"""
        try:
            settings = await self.settings_repo.get_settings(user_id)
            
            if not settings:
                # Return default settings
                return {
                    "user_id": user_id,
                    "enabled_channels": [NotificationChannel.IN_APP],
                    "quiet_hours": {},
                    "min_priority": NotificationPriority.LOW,
                    "email_address": None,
                    "phone_number": None,
                    "webhook_url": None,
                    "slack_webhook": None,
                    "discord_webhook": None
                }
            
            return settings
            
        except Exception as e:
            raise e
    
    async def update_settings(self, user_id: int, settings: NotificationSettingsRequest) -> Dict[str, Any]:
        """Update notification settings for a user"""
        try:
            success = await self.settings_repo.update_settings(user_id, settings)
            
            if not success:
                raise NotFoundError(f"Settings for user {user_id} not found")
            
            # Return updated settings
            updated_settings = await self.settings_repo.get_settings(user_id)
            
            return {
                "success": True,
                "settings": updated_settings
            }
            
        except Exception as e:
            raise e
    
    async def create_settings(self, settings: NotificationSettingsRequest) -> Dict[str, Any]:
        """Create notification settings for a user"""
        try:
            settings_id = await self.settings_repo.create_settings(settings)
            
            # Return created settings
            created_settings = await self.settings_repo.get_settings(settings.user_id)
            
            return {
                "success": True,
                "settings": created_settings
            }
            
        except Exception as e:
            raise e
    
    async def get_users_with_enabled_channel(self, channel: NotificationChannel) -> List[int]:
        """Get all users who have enabled a specific channel"""
        try:
            return await self.settings_repo.get_users_with_enabled_channel(channel)
        except Exception as e:
            raise e


class NotificationDigestService:
    """Service for notification digest management"""
    
    def __init__(self, digest_repo: NotificationDigestRepository, notification_repo: NotificationRepository):
        self.digest_repo = digest_repo
        self.notification_repo = notification_repo
    
    async def create_digest(self, request: NotificationDigestRequest) -> Dict[str, Any]:
        """Create a notification digest"""
        try:
            # Get notifications for digest
            notifications = await self.notification_repo.get_all_notifications(
                user_id=request.user_id,
                types=request.types,
                read=not request.include_read,
                limit=request.max_items
            )
            
            # Create digest
            digest_id = await self.digest_repo.create_digest(request)
            
            return {
                "success": True,
                "digest_id": digest_id,
                "notification_count": len(notifications)
            }
            
        except Exception as e:
            raise e
    
    async def get_digests(self, user_id: int, frequency: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get digests for a user"""
        try:
            return await self.digest_repo.get_digests(user_id, frequency)
        except Exception as e:
            raise e
    
    async def get_latest_digest(self, user_id: int, frequency: str) -> Optional[Dict[str, Any]]:
        """Get latest digest for a user and frequency"""
        try:
            return await self.digest_repo.get_latest_digest(user_id, frequency)
        except Exception as e:
            raise e
    
    async def mark_digest_sent(self, digest_id: int) -> Dict[str, Any]:
        """Mark digest as sent"""
        try:
            success = await self.digest_repo.mark_digest_sent(digest_id)
            
            if not success:
                raise NotFoundError(f"Digest {digest_id} not found")
            
            return {
                "success": True,
                "message": f"Digest {digest_id} marked as sent"
            }
            
        except Exception as e:
            raise e


class NotificationDeliveryService:
    """Service for notification delivery operations"""
    
    def __init__(self, delivery_repo: NotificationDeliveryRepository):
        self.delivery_repo = delivery_repo
    
    async def send_notification(self, notification_data: NotificationCreateRequest) -> Dict[str, Any]:
        """Send a single notification"""
        try:
            result = await self.delivery_repo.send_notification(notification_data)
            
            return {
                "success": True,
                "delivery_id": result.get("delivery_id"),
                "status": result.get("status", "PENDING")
            }
            
        except Exception as e:
            raise e
    
    async def send_bulk_notifications(self, request: NotificationSendRequest) -> Dict[str, Any]:
        """Send notifications to multiple users"""
        try:
            result = await self.delivery_repo.send_bulk_notifications(request)
            
            return {
                "success": True,
                "sent_count": result.get("sent_count", 0),
                "delivery_status": result.get("status", "PENDING")
            }
            
        except Exception as e:
            raise e
    
    async def get_delivery_status(self, notification_id: int) -> Dict[str, Any]:
        """Get delivery status for a notification"""
        try:
            return await self.delivery_repo.get_delivery_status(notification_id)
        except Exception as e:
            raise e
    
    async def retry_failed_notifications(self, max_retries: int = 3) -> Dict[str, Any]:
        """Retry failed notifications"""
        try:
            count = await self.delivery_repo.retry_failed_notifications(max_retries)
            
            return {
                "success": True,
                "retried_count": count,
                "message": f"Retried {count} failed notifications"
            }
            
        except Exception as e:
            raise e
    
    async def get_delivery_stats(self, channel: Optional[NotificationChannel] = None) -> Dict[str, Any]:
        """Get delivery statistics by channel"""
        try:
            return await self.delivery_repo.get_delivery_stats(channel)
        except Exception as e:
            raise e
