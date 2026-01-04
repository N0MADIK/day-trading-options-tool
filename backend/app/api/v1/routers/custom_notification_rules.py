"""Custom Notification Rules API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
from app.models.custom_notification_rule import CustomNotificationRule
from app.schemas.custom_notification_rule import (
    CustomNotificationRuleCreate,
    CustomNotificationRuleUpdate,
    CustomNotificationRuleResponse
)

router = APIRouter(prefix="/custom-notification-rules", tags=["custom-notification-rules"])


@router.get("/", response_model=List[CustomNotificationRuleResponse])
async def list_rules(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """List all custom notification rules for the current user"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(CustomNotificationRule).where(CustomNotificationRule.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/", response_model=CustomNotificationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: CustomNotificationRuleCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new custom notification rule"""
    user_id = UUID(current_user_id)
    
    rule = CustomNotificationRule(
        user_id=user_id,
        rule_name=rule_data.rule_name,
        rule_type=rule_data.rule_type,
        indicator_type=rule_data.indicator_type,
        conditions=rule_data.conditions or {},
        frequency=rule_data.frequency,
        urgency_level=rule_data.urgency_level,
        is_enabled=rule_data.is_enabled,
        sensitivity=rule_data.sensitivity,
        quiet_hours_start=rule_data.quiet_hours_start,
        quiet_hours_end=rule_data.quiet_hours_end,
        notify_email=rule_data.notify_email,
        notify_push=rule_data.notify_push,
        notify_sms=rule_data.notify_sms
    )
    
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=CustomNotificationRuleResponse)
async def get_rule(
    rule_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a single rule by ID"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(CustomNotificationRule).where(
            CustomNotificationRule.id == rule_id,
            CustomNotificationRule.user_id == user_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    return rule


@router.put("/{rule_id}", response_model=CustomNotificationRuleResponse)
async def update_rule(
    rule_id: UUID,
    rule_data: CustomNotificationRuleUpdate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a custom notification rule"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(CustomNotificationRule).where(
            CustomNotificationRule.id == rule_id,
            CustomNotificationRule.user_id == user_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    update_dict = rule_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(rule, field, value)
    
    await session.commit()
    await session.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a custom notification rule"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(CustomNotificationRule).where(
            CustomNotificationRule.id == rule_id,
            CustomNotificationRule.user_id == user_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    await session.delete(rule)
    await session.commit()


@router.post("/{rule_id}/test")
async def test_rule(
    rule_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Test a rule trigger (useful for debugging)"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(CustomNotificationRule).where(
            CustomNotificationRule.id == rule_id,
            CustomNotificationRule.user_id == user_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    # TODO: Implement actual rule evaluation against current market data
    return {
        "rule_id": str(rule_id),
        "rule_name": rule.rule_name,
        "would_trigger": False,
        "message": "Test complete - rule evaluation not yet implemented"
    }
