"""Notification Settings API router - Simple user preferences"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
from app.models.notification_settings import NotificationSettings
from app.schemas.notification_settings import (
    NotificationSettingsUpdate,
    NotificationSettingsResponse
)

router = APIRouter(prefix="/notification-settings", tags=["notification-settings"])


@router.get("/", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user's notification settings"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings for user
        settings = NotificationSettings(
            user_id=user_id,
            email_notifications=True,
            push_notifications=False,
            price_alerts=True,
            goal_progress_alerts=True,
            weekly_reports=True,
            daily_summary=False
        )
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    
    return settings


@router.put("/", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    update_data: NotificationSettingsUpdate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update current user's notification settings"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create with provided settings
        settings = NotificationSettings(
            user_id=user_id,
            **update_data.model_dump(exclude_unset=True)
        )
        session.add(settings)
    else:
        # Update existing settings
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(settings, field, value)
    
    await session.commit()
    await session.refresh(settings)
    return settings
