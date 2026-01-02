from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional

from app.services.notification_service import (
    NotificationService, NotificationTemplateService, NotificationSettingsService,
    NotificationDigestService, NotificationDeliveryService
)
from app.repositories.sqlalchemy.notification_repo import (
    SQLAlchemyNotificationRepository, SQLAlchemyNotificationTemplateRepository,
    SQLAlchemyNotificationSettingsRepository, SQLAlchemyNotificationDeliveryRepository,
    SQLAlchemyNotificationDigestRepository
)
from app.infrastructure.db import get_async_session
from app.schemas.notifications import (
    NotificationCreateRequest, NotificationUpdateRequest, NotificationType,
    NotificationPriority, NotificationChannel, NotificationStatus,
    NotificationListRequest, NotificationTemplateCreateRequest,
    NotificationBatchRequest, NotificationSendRequest,
    NotificationSettingsRequest, NotificationDigestRequest
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError

# Create routers for different notification types
router = APIRouter(prefix="/notifications", tags=["notifications"])

templates_router = APIRouter(prefix="/templates", tags=["notification-templates"])
settings_router = APIRouter(prefix="/settings", tags=["notification-settings"])
digest_router = APIRouter(prefix="/digests", tags=["notification-digests"])
delivery_router = APIRouter(prefix="/delivery", tags=["notification-delivery"])

# Dependencies for services
async def get_notification_service() -> NotificationService:
    """Get notification service with repository"""
    session = await get_async_session()
    notification_repo = SQLAlchemyNotificationRepository(session)
    template_repo = SQLAlchemyNotificationTemplateRepository(session)
    settings_repo = SQLAlchemyNotificationSettingsRepository(session)
    delivery_repo = SQLAlchemyNotificationDeliveryRepository(session)
    digest_repo = SQLAlchemyNotificationDigestRepository(session)
    return NotificationService(
        notification_repo, template_repo, settings_repo, delivery_repo, digest_repo
    )

async def get_template_service() -> NotificationTemplateService:
    """Get template service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyNotificationTemplateRepository(session)
    return NotificationTemplateService(repository)

async def get_settings_service() -> NotificationSettingsService:
    """Get settings service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyNotificationSettingsRepository(session)
    return NotificationSettingsService(repository)

async def get_digest_service() -> NotificationDigestService:
    """Get digest service with repository"""
    session = await get_async_session()
    notification_repo = SQLAlchemyNotificationRepository(session)
    digest_repo = SQLAlchemyNotificationDigestRepository(session)
    return NotificationDigestService(digest_repo, notification_repo)

async def get_delivery_service() -> NotificationDeliveryService:
    """Get delivery service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyNotificationDeliveryRepository(session)
    return NotificationDeliveryService(repository)


# Standard Notification Endpoints
@router.post("/", response_model=dict)
async def create_notification(
    notification_data: NotificationCreateRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Create a new notification"""
    try:
        return await service.create_notification(notification_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[dict])
async def list_notifications(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    priority: Optional[NotificationPriority] = Query(None, description="Filter by priority"),
    channel: Optional[NotificationChannel] = Query(None, description="Filter by channel"),
    read: Optional[bool] = Query(None, description="Filter by read status"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: NotificationService = Depends(get_notification_service)
):
    """List notifications with optional filters"""
    try:
        request = NotificationListRequest(
            user_id=user_id,
            type=type,
            priority=priority,
            channel=channel,
            read=read,
            limit=limit,
            offset=offset
        )
        return await service.list_notifications(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}", response_model=dict)
async def get_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service)
):
    """Get a single notification by ID"""
    try:
        return await service.get_notification_by_id(notification_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}", response_model=dict)
async def update_notification(
    notification_id: int,
    updates: NotificationUpdateRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Update a notification"""
    try:
        return await service.update_notification(notification_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service)
):
    """Delete a notification"""
    try:
        return await service.delete_notification(notification_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read"""
    try:
        return await service.mark_notification_read(notification_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/read", response_model=dict)
async def mark_notifications_read(
    notification_ids: List[int] = Body(..., description="List of notification IDs"),
    service: NotificationService = Depends(get_notification_service)
):
    """Mark multiple notifications as read"""
    try:
        return await service.mark_notifications_read(notification_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read", response_model=dict)
async def mark_all_read(
    user_id: Optional[int] = Body(None, description="User ID (null for all users)"),
    service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read for a user or all users"""
    try:
        return await service.mark_all_read(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    user_id: Optional[int] = Query(None, description="User ID (null for all users)"),
    service: NotificationService = Depends(get_notification_service)
):
    """Get count of unread notifications"""
    try:
        count = await service.get_unread_count(user_id)
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_notification_statistics(
    user_id: Optional[int] = Query(None, description="User ID (null for all users)"),
    service: NotificationService = Depends(get_notification_service)
):
    """Get aggregate notification statistics"""
    try:
        return await service.get_notification_stats(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[dict])
async def search_notifications(
    q: str = Query(..., min_length=2, description="Search query (title or message)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    service: NotificationService = Depends(get_notification_service)
):
    """Search notifications by title or message"""
    try:
        return await service.search_notifications(q, user_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/batch/update", response_model=dict)
async def batch_update_notifications(
    batch_data: NotificationBatchRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Update multiple notifications at once"""
    try:
        return await service.batch_update_notifications(batch_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/batch/delete", response_model=dict)
async def batch_delete_notifications(
    batch_data: NotificationBatchRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Delete multiple notifications at once"""
    try:
        return await service.batch_delete_notifications(batch_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup", response_model=dict)
async def cleanup_expired_notifications(
    service: NotificationService = Depends(get_notification_service)
):
    """Delete expired notifications"""
    try:
        return await service.cleanup_expired_notifications()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Template Endpoints
@templates_router.post("/", response_model=dict)
async def create_template(
    template_data: NotificationTemplateCreateRequest,
    service: NotificationTemplateService = Depends(get_template_service)
):
    """Create a new notification template"""
    try:
        return await service.create_template(template_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@templates_router.get("/", response_model=List[dict])
async def list_templates(
    type: Optional[NotificationType] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: NotificationTemplateService = Depends(get_template_service)
):
    """List templates with optional filters"""
    try:
        return await service.list_templates(type, is_active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@templates_router.get("/active", response_model=List[dict])
async def get_active_templates(
    service: NotificationTemplateService = Depends(get_template_service)
):
    """Get all active templates"""
    try:
        return await service.get_active_templates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@templates_router.get("/{template_id}", response_model=dict)
async def get_template(
    template_id: int,
    service: NotificationTemplateService = Depends(get_template_service)
):
    """Get a single template by ID"""
    try:
        return await service.get_template_by_id(template_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@templates_router.put("/{template_id}", response_model=dict)
async def update_template(
    template_id: int,
    updates: dict = Body(..., description="Template updates"),
    service: NotificationTemplateService = Depends(get_template_service)
):
    """Update a template"""
    try:
        return await service.update_template(template_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@templates_router.delete("/{template_id}", response_model=dict)
async def delete_template(
    template_id: int,
    service: NotificationTemplateService = Depends(get_template_service)
):
    """Delete a template"""
    try:
        return await service.delete_template(template_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@templates_router.post("/{template_id}/render", response_model=dict)
async def render_template(
    template_id: int,
    variables: dict = Body(..., description="Template variables"),
    service: NotificationTemplateService = Depends(get_template_service)
):
    """Render a template with provided variables"""
    try:
        return await service.render_template(template_id, variables)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Settings Endpoints
@settings_router.get("/{user_id}", response_model=dict)
async def get_settings(
    user_id: int,
    service: NotificationSettingsService = Depends(get_settings_service)
):
    """Get notification settings for a user"""
    try:
        return await service.get_settings(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@settings_router.put("/{user_id}", response_model=dict)
async def update_settings(
    user_id: int,
    settings: NotificationSettingsRequest,
    service: NotificationSettingsService = Depends(get_settings_service)
):
    """Update notification settings for a user"""
    try:
        return await service.update_settings(user_id, settings)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@settings_router.post("/", response_model=dict)
async def create_settings(
    settings: NotificationSettingsRequest,
    service: NotificationSettingsService = Depends(get_settings_service)
):
    """Create notification settings for a user"""
    try:
        return await service.create_settings(settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@settings_router.get("/channel/{channel}/users", response_model=List[int])
async def get_users_with_enabled_channel(
    channel: NotificationChannel,
    service: NotificationSettingsService = Depends(get_settings_service)
):
    """Get all users who have enabled a specific channel"""
    try:
        return await service.get_users_with_enabled_channel(channel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Digest Endpoints
@digest_router.post("/", response_model=dict)
async def create_digest(
    request: NotificationDigestRequest,
    service: NotificationDigestService = Depends(get_digest_service)
):
    """Create a notification digest"""
    try:
        return await service.create_digest(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@digest_router.get("/{user_id}", response_model=List[dict])
async def get_digests(
    user_id: int,
    frequency: Optional[str] = Query(None, description="Digest frequency"),
    service: NotificationDigestService = Depends(get_digest_service)
):
    """Get digests for a user"""
    try:
        return await service.get_digests(user_id, frequency)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@digest_router.get("/{user_id}/latest", response_model=dict)
async def get_latest_digest(
    user_id: int,
    frequency: str = Query(..., description="Digest frequency"),
    service: NotificationDigestService = Depends(get_digest_service)
):
    """Get latest digest for a user and frequency"""
    try:
        result = await service.get_latest_digest(user_id, frequency)
        if not result:
            raise HTTPException(status_code=404, detail="Digest not found")
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@digest_router.post("/{digest_id}/sent", response_model=dict)
async def mark_digest_sent(
    digest_id: int,
    service: NotificationDigestService = Depends(get_digest_service)
):
    """Mark digest as sent"""
    try:
        return await service.mark_digest_sent(digest_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delivery Endpoints
@delivery_router.post("/send", response_model=dict)
async def send_notification(
    notification_data: NotificationSendRequest,
    service: NotificationDeliveryService = Depends(get_delivery_service)
):
    """Send a single notification"""
    try:
        return await service.send_notification(notification_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@delivery_router.post("/bulk-send", response_model=dict)
async def send_bulk_notifications(
    request: NotificationSendRequest,
    service: NotificationDeliveryService = Depends(get_delivery_service)
):
    """Send notifications to multiple users"""
    try:
        return await service.send_bulk_notifications(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@delivery_router.get("/status/{notification_id}", response_model=dict)
async def get_delivery_status(
    notification_id: int,
    service: NotificationDeliveryService = Depends(get_delivery_service)
):
    """Get delivery status for a notification"""
    try:
        return await service.get_delivery_status(notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@delivery_router.post("/retry-failed", response_model=dict)
async def retry_failed_notifications(
    max_retries: int = Query(3, ge=1, le=10, description="Maximum number of retries"),
    service: NotificationDeliveryService = Depends(get_delivery_service)
):
    """Retry failed notifications"""
    try:
        return await service.retry_failed_notifications(max_retries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@delivery_router.get("/stats", response_model=dict)
async def get_delivery_stats(
    channel: Optional[NotificationChannel] = Query(None, description="Filter by channel"),
    service: NotificationDeliveryService = Depends(get_delivery_service)
):
    """Get delivery statistics by channel"""
    try:
        return await service.get_delivery_stats(channel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Include sub-routers
router.include_router(templates_router)
router.include_router(settings_router)
router.include_router(digest_router)
router.include_router(delivery_router)
