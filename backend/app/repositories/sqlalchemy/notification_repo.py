from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.domain.models import Notification, NotificationTemplate, NotificationSettings, NotificationDigest
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class SQLAlchemyNotificationRepository(NotificationRepository):
    """SQLAlchemy implementation of notification repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_notification(self, notification_data: NotificationCreateRequest) -> int:
        """Create a new notification and return its ID"""
        try:
            notification = Notification(
                user_id=notification_data.user_id,
                type=notification_data.type,
                title=notification_data.title,
                message=notification_data.message,
                priority=notification_data.priority,
                channel=notification_data.channel,
                data=json.dumps(notification_data.data) if notification_data.data else None,
                read=notification_data.read,
                expires_at=notification_data.expires_at,
                status=NotificationStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            self.session.add(notification)
            await self.session.flush()
            await self.session.refresh(notification)
            
            return notification.id
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_notification_by_id(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get a single notification by ID"""
        try:
            result = await self.session.execute(
                sa.select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            
            if not notification:
                return None
            
            return {
                'id': notification.id,
                'user_id': notification.user_id,
                'type': notification.type,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'channel': notification.channel,
                'data': json.loads(notification.data) if notification.data else None,
                'read': notification.read,
                'sent_at': notification.sent_at,
                'delivered_at': notification.delivered_at,
                'read_at': notification.read_at,
                'expires_at': notification.expires_at,
                'status': notification.status,
                'created_at': notification.created_at,
                'updated_at': notification.updated_at
            }
            
        except Exception as e:
            raise e
    
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
        try:
            query = sa.select(Notification).order_by(Notification.created_at.desc())
            
            # Apply filters
            if user_id is not None:
                query = query.where(Notification.user_id == user_id)
            if type:
                query = query.where(Notification.type == type)
            if priority:
                query = query.where(Notification.priority == priority)
            if channel:
                query = query.where(Notification.channel == channel)
            if read is not None:
                query = query.where(Notification.read == read)
            if expires_before:
                query = query.where(Notification.expires_at < expires_before)
            if created_after:
                query = query.where(Notification.created_at > created_after)
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            notifications = result.scalars().all()
            
            notification_list = []
            for notification in notifications:
                notification_list.append({
                    'id': notification.id,
                    'user_id': notification.user_id,
                    'type': notification.type,
                    'title': notification.title,
                    'message': notification.message,
                    'priority': notification.priority,
                    'channel': notification.channel,
                    'data': json.loads(notification.data) if notification.data else None,
                    'read': notification.read,
                    'sent_at': notification.sent_at,
                    'delivered_at': notification.delivered_at,
                    'read_at': notification.read_at,
                    'expires_at': notification.expires_at,
                    'status': notification.status,
                    'created_at': notification.created_at,
                    'updated_at': notification.updated_at
                })
            
            return notification_list
            
        except Exception as e:
            raise e
    
    async def update_notification(self, notification_id: int, updates: NotificationUpdateRequest) -> bool:
        """Update a notification"""
        try:
            notification = await self.session.get(Notification, notification_id)
            if not notification:
                return False
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(notification, field):
                    setattr(notification, field, value)
            
            notification.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        try:
            notification = await self.session.get(Notification, notification_id)
            if not notification:
                return False
            
            await self.session.delete(notification)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read"""
        try:
            notification = await self.session.get(Notification, notification_id)
            if not notification:
                return False
            
            notification.read = True
            notification.read_at = datetime.utcnow()
            notification.updated_at = datetime.utcnow()
            
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def mark_notifications_read(self, notification_ids: List[int]) -> int:
        """Mark multiple notifications as read"""
        try:
            stmt = (
                sa.update(Notification)
                .where(Notification.id.in_(notification_ids))
                .values(
                    read=True,
                    read_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def mark_all_read(self, user_id: Optional[int] = None) -> int:
        """Mark all notifications as read for a user or all users"""
        try:
            query = sa.update(Notification).where(Notification.read == False)
            if user_id is not None:
                query = query.where(Notification.user_id == user_id)
            
            stmt = query.values(
                read=True,
                read_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_unread_count(self, user_id: Optional[int] = None) -> int:
        """Get count of unread notifications for a user or all users"""
        try:
            query = sa.select(sa.func.count(Notification.id)).where(Notification.read == False)
            if user_id is not None:
                query = query.where(Notification.user_id == user_id)
            
            result = await self.session.execute(query)
            return result.scalar()
            
        except Exception as e:
            raise e
    
    async def get_notification_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregate notification statistics"""
        try:
            # Base query
            base_query = sa.select(Notification)
            if user_id is not None:
                base_query = base_query.where(Notification.user_id == user_id)
            
            # Total notifications
            total_result = await self.session.execute(
                base_query.with_only_columns(sa.func.count(Notification.id))
            )
            total = total_result.scalar()
            
            # Unread notifications
            unread_result = await self.session.execute(
                base_query.with_only_columns(sa.func.count(Notification.id))
                .where(Notification.read == False)
            )
            unread = unread_result.scalar()
            
            # Read notifications
            read_result = await self.session.execute(
                base_query.with_only_columns(sa.func.count(Notification.id))
                .where(Notification.read == True)
            )
            read = read_result.scalar()
            
            # By status
            status_result = await self.session.execute(
                base_query.with_only_columns(
                    Notification.status,
                    sa.func.count(Notification.id).label('count')
                )
                .group_by(Notification.status)
            )
            status_rows = status_result.all()
            
            status_counts = {}
            for status, count in status_rows:
                status_counts[status] = count
            
            # By priority
            priority_result = await self.session.execute(
                base_query.with_only_columns(
                    Notification.priority,
                    sa.func.count(Notification.id).label('count')
                )
                .group_by(Notification.priority)
            )
            priority_rows = priority_result.all()
            
            priority_counts = {}
            for priority, count in priority_rows:
                priority_counts[priority] = count
            
            # By channel
            channel_result = await self.session.execute(
                base_query.with_only_columns(
                    Notification.channel,
                    sa.func.count(Notification.id).label('count')
                )
                .group_by(Notification.channel)
            )
            channel_rows = channel_result.all()
            
            channel_counts = {}
            for channel, count in channel_rows:
                channel_counts[channel] = count
            
            # Average delivery time (simplified)
            delivery_result = await self.session.execute(
                base_query.with_only_columns(
                    sa.func.avg(
                        sa.extract('epoch', Notification.delivered_at) - 
                        sa.extract('epoch', Notification.sent_at)
                    ).label('avg_delivery_time')
                )
                .where(
                    sa.and_(
                        Notification.delivered_at.isnot(None),
                        Notification.sent_at.isnot(None)
                    )
                )
            )
            avg_delivery_time = delivery_result.scalar()
            
            # Delivery success rate
            delivered_result = await self.session.execute(
                base_query.with_only_columns(
                    sa.func.count(Notification.id).label('total'),
                    sa.func.count(Notification.id).label('delivered')
                )
                .where(Notification.status == NotificationStatus.DELIVERED)
            )
            delivered_row = delivered_result.first()
            
            if delivered_row and delivered_row.total > 0:
                delivery_success_rate = (delivered_row.delivered / delivered_row.total) * 100
            else:
                delivery_success_rate = None
            
            return {
                "total_notifications": total or 0,
                "unread_notifications": unread or 0,
                "read_notifications": read or 0,
                "pending_notifications": status_counts.get(NotificationStatus.PENDING, 0),
                "failed_notifications": status_counts.get(NotificationStatus.FAILED, 0),
                "notifications_by_type": status_counts,
                "notifications_by_priority": priority_counts,
                "notifications_by_channel": channel_counts,
                "avg_delivery_time_seconds": round(avg_delivery_time, 2) if avg_delivery_time else None,
                "delivery_success_rate": round(delivery_success_rate, 1) if delivery_success_rate else None
            }
            
        except Exception as e:
            raise e
    
    async def search_notifications(self, query: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search notifications by title or message"""
        try:
            search_pattern = f"%{query.upper()}%"
            
            base_query = sa.select(Notification)
            if user_id is not None:
                base_query = base_query.where(Notification.user_id == user_id)
            
            result = await self.session.execute(
                base_query.where(
                    sa.or_(
                        Notification.title.ilike(search_pattern),
                        Notification.message.ilike(search_pattern)
                    )
                )
                .order_by(Notification.created_at.desc())
            )
            
            notifications = result.scalars().all()
            
            notification_list = []
            for notification in notifications:
                notification_list.append({
                    'id': notification.id,
                    'user_id': notification.user_id,
                    'type': notification.type,
                    'title': notification.title,
                    'message': notification.message,
                    'priority': notification.priority,
                    'channel': notification.channel,
                    'created_at': notification.created_at
                })
            
            return notification_list
            
        except Exception as e:
            raise e
    
    async def batch_update_notifications(self, notification_ids: List[int], updates: Dict[str, Any]) -> int:
        """Update multiple notifications at once"""
        try:
            stmt = (
                sa.update(Notification)
                .where(Notification.id.in_(notification_ids))
                .values(**updates)
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def batch_delete_notifications(self, notification_ids: List[int]) -> int:
        """Delete multiple notifications at once"""
        try:
            stmt = sa.delete(Notification).where(Notification.id.in_(notification_ids))
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def cleanup_expired_notifications(self) -> int:
        """Delete expired notifications"""
        try:
            stmt = sa.delete(Notification).where(
                sa.and_(
                    Notification.expires_at < datetime.utcnow(),
                    Notification.read == False
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e


class SQLAlchemyNotificationTemplateRepository(NotificationTemplateRepository):
    """SQLAlchemy implementation of notification template repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_template(self, template_data: NotificationTemplateCreateRequest) -> int:
        """Create a new notification template and return its ID"""
        try:
            template = NotificationTemplate(
                name=template_data.name,
                type=template_data.type,
                title_template=template_data.title_template,
                message_template=template_data.message_template,
                default_priority=template_data.default_priority,
                default_channel=template_data.default_channel,
                variables=json.dumps(template_data.variables),
                description=template_data.description,
                is_active=template_data.is_active,
                created_at=datetime.utcnow()
            )
            
            self.session.add(template)
            await self.session.flush()
            await self.session.refresh(template)
            
            return template.id
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a single template by ID"""
        try:
            result = await self.session.execute(
                sa.select(NotificationTemplate).where(NotificationTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return None
            
            return {
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'title_template': template.title_template,
                'message_template': template.message_template,
                'default_priority': template.default_priority,
                'default_channel': template.default_channel,
                'variables': json.loads(template.variables) if template.variables else [],
                'description': template.description,
                'is_active': template.is_active,
                'created_at': template.created_at,
                'updated_at': template.updated_at
            }
            
        except Exception as e:
            raise e
    
    async def get_all_templates(
        self,
        type: Optional[NotificationType] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all templates with optional filters"""
        try:
            query = sa.select(NotificationTemplate).order_by(NotificationTemplate.created_at.desc())
            
            # Apply filters
            if type:
                query = query.where(NotificationTemplate.type == type)
            if is_active is not None:
                query = query.where(NotificationTemplate.is_active == is_active)
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            templates = result.scalars().all()
            
            template_list = []
            for template in templates:
                template_list.append({
                    'id': template.id,
                    'name': template.name,
                    'type': template.type,
                    'title_template': template.title_template,
                    'message_template': template.message_template,
                    'default_priority': template.default_priority,
                    'default_channel': template.default_channel,
                    'variables': json.loads(template.variables) if template.variables else [],
                    'description': template.description,
                    'is_active': template.is_active,
                    'created_at': template.created_at,
                    'updated_at': template.updated_at
                })
            
            return template_list
            
        except Exception as e:
            raise e
    
    async def update_template(self, template_id: int, updates: Dict[str, Any]) -> bool:
        """Update a template"""
        try:
            template = await self.session.get(NotificationTemplate, template_id)
            if not template:
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(template, field):
                    if field == 'variables' and isinstance(value, list):
                        setattr(template, field, json.dumps(value))
                    else:
                        setattr(template, field, value)
            
            template.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        try:
            template = await self.session.get(NotificationTemplate, template_id)
            if not template:
                return False
            
            await self.session.delete(template)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_active_templates(self) -> List[Dict[str, Any]]:
        """Get all active templates"""
        try:
            result = await self.session.execute(
                sa.select(NotificationTemplate)
                .where(NotificationTemplate.is_active == True)
                .order_by(NotificationTemplate.name)
            )
            
            templates = result.scalars().all()
            
            template_list = []
            for template in templates:
                template_list.append({
                    'id': template.id,
                    'name': template.name,
                    'type': template.type,
                    'is_active': template.is_active,
                    'created_at': template.created_at
                })
            
            return template_list
            
        except Exception as e:
            raise e
    
    async def render_template(self, template_id: int, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Render a template with provided variables"""
        try:
            template = await self.session.get(NotificationTemplate, template_id)
            if not template:
                raise NotFoundError(f"Template {template_id} not found")
            
            # Simple template rendering (in production, use a proper templating engine)
            title = template.title_template
            message = template.message_template
            
            # Replace variables
            template_vars = json.loads(template.variables) if template.variables else []
            for var in template_vars:
                placeholder = f"{{{var}}}"
                value = str(variables.get(var, f"{{{var}}}"))
                title = title.replace(placeholder, value)
                message = message.replace(placeholder, value)
            
            return {
                'template_id': template_id,
                'rendered_title': title,
                'rendered_message': message,
                'used_variables': variables
            }
            
        except Exception as e:
            raise e


class SQLAlchemyNotificationSettingsRepository(NotificationSettingsRepository):
    """SQLAlchemy implementation of notification settings repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get notification settings for a user"""
        try:
            result = await self.session.execute(
                sa.select(NotificationSettings).where(NotificationSettings.user_id == user_id)
            )
            settings = result.scalar_one_or_none()
            
            if not settings:
                return None
            
            return {
                'user_id': settings.user_id,
                'enabled_channels': json.loads(settings.enabled_channels) if settings.enabled_channels else [],
                'quiet_hours': json.loads(settings.quiet_hours) if settings.quiet_hours else {},
                'min_priority': settings.min_priority,
                'email_address': settings.email_address,
                'phone_number': settings.phone_number,
                'webhook_url': settings.webhook_url,
                'slack_webhook': settings.slack_webhook,
                'discord_webhook': settings.discord_webhook,
                'created_at': settings.created_at,
                'updated_at': settings.updated_at
            }
            
        except Exception as e:
            raise e
    
    async def update_settings(self, user_id: int, settings: NotificationSettingsRequest) -> bool:
        """Update notification settings for a user"""
        try:
            existing_settings = await self.session.get(NotificationSettings, user_id)
            
            if existing_settings:
                # Update existing settings
                existing_settings.enabled_channels = json.dumps(settings.enabled_channels)
                existing_settings.quiet_hours = json.dumps(settings.quiet_hours)
                existing_settings.min_priority = settings.min_priority
                existing_settings.email_address = settings.email_address
                existing_settings.phone_number = settings.phone_number
                existing_settings.webhook_url = settings.webhook_url
                existing_settings.slack_webhook = settings.slack_webhook
                existing_settings.discord_webhook = settings.discord_webhook
                existing_settings.updated_at = datetime.utcnow()
                
                await self.session.commit()
                return True
            else:
                # Create new settings
                new_settings = NotificationSettings(
                    user_id=user_id,
                    enabled_channels=json.dumps(settings.enabled_channels),
                    quiet_hours=json.dumps(settings.quiet_hours),
                    min_priority=settings.min_priority,
                    email_address=settings.email_address,
                    phone_number=settings.phone_number,
                    webhook_url=settings.webhook_url,
                    slack_webhook=settings.slack_webhook,
                    discord_webhook=settings.discord_webhook,
                    created_at=datetime.utcnow()
                )
                
                self.session.add(new_settings)
                await self.session.commit()
                return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def create_settings(self, settings: NotificationSettingsRequest) -> int:
        """Create notification settings for a user"""
        try:
            new_settings = NotificationSettings(
                user_id=settings.user_id,
                enabled_channels=json.dumps(settings.enabled_channels),
                quiet_hours=json.dumps(settings.quiet_hours),
                min_priority=settings.min_priority,
                email_address=settings.email_address,
                phone_number=settings.phone_number,
                webhook_url=settings.webhook_url,
                slack_webhook=settings.slack_webhook,
                discord_webhook=settings.discord_webhook,
                created_at=datetime.utcnow()
            )
            
            self.session.add(new_settings)
            await self.session.flush()
            await self.session.refresh(new_settings)
            
            return new_settings.id
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_users_with_enabled_channel(self, channel: NotificationChannel) -> List[int]:
        """Get all users who have enabled a specific channel"""
        try:
            result = await self.session.execute(
                sa.select(NotificationSettings.user_id)
                .where(
                    sa.text(f"json_extract(enabled_channels, '$') LIKE '%{channel}%'")
                )
            )
            
            user_ids = [row[0] for row in result.all()]
            return user_ids
            
        except Exception as e:
            raise e


# Placeholder implementations for delivery and digest repositories
# These would typically integrate with external services (email, SMS, webhooks, etc.)

class SQLAlchemyNotificationDeliveryRepository(NotificationDeliveryRepository):
    """SQLAlchemy implementation of notification delivery repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def send_notification(self, notification_data: NotificationCreateRequest) -> Dict[str, Any]:
        """Send a single notification"""
        # This would integrate with actual delivery services
        # For now, just mark as sent
        try:
            notification = await self.session.get(Notification, 1)  # Placeholder
            if notification:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                await self.session.commit()
                return {"success": True, "delivery_id": notification.id}
            return {"success": False, "error": "Notification not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_bulk_notifications(self, request: NotificationSendRequest) -> Dict[str, Any]:
        """Send notifications to multiple users"""
        # Placeholder implementation
        return {"success": True, "sent_count": len(request.user_ids)}
    
    async def get_delivery_status(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get delivery status for a notification"""
        # Placeholder implementation
        return {"notification_id": notification_id, "status": "SENT"}
    
    async def retry_failed_notifications(self, max_retries: int = 3) -> int:
        """Retry failed notifications"""
        # Placeholder implementation
        return 0
    
    async def get_delivery_stats(self, channel: Optional[NotificationChannel] = None) -> Dict[str, Any]:
        """Get delivery statistics by channel"""
        # Placeholder implementation
        return {"channel": channel, "total_sent": 100, "success_rate": 95.5}


class SQLAlchemyNotificationDigestRepository(NotificationDigestRepository):
    """SQLAlchemy implementation of notification digest repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_digest(self, request: NotificationDigestRequest) -> int:
        """Create a notification digest"""
        # Placeholder implementation
        return 1
    
    async def get_digests(self, user_id: int, frequency: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get digests for a user"""
        # Placeholder implementation
        return []
    
    async def get_latest_digest(self, user_id: int, frequency: str) -> Optional[Dict[str, Any]]:
        """Get latest digest for a user and frequency"""
        # Placeholder implementation
        return None
    
    async def mark_digest_sent(self, digest_id: int) -> bool:
        """Mark digest as sent"""
        # Placeholder implementation
        return True
