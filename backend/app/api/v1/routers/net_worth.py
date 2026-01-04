"""Net Worth tracking API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
from app.models.net_worth import NetWorthHistory, NetWorthGoal
from app.schemas.net_worth import (
    NetWorthHistoryResponse,
    NetWorthSnapshotCreate,
    NetWorthGoalCreate,
    NetWorthGoalUpdate,
    NetWorthGoalResponse,
    NetWorthSummary
)

router = APIRouter(prefix="/net-worth", tags=["net-worth"])


@router.get("/history", response_model=List[NetWorthHistoryResponse])
async def get_net_worth_history(
    limit: int = 30,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get net worth history for the current user"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(NetWorthHistory)
        .where(NetWorthHistory.user_id == user_id)
        .order_by(desc(NetWorthHistory.recorded_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/snapshot", response_model=NetWorthHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    snapshot_data: NetWorthSnapshotCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Record a net worth snapshot"""
    user_id = UUID(current_user_id)
    
    snapshot = NetWorthHistory(
        user_id=user_id,
        total_net_worth=snapshot_data.total_net_worth,
        total_assets=snapshot_data.total_assets,
        total_liabilities=snapshot_data.total_liabilities or 0,
        breakdown=snapshot_data.breakdown or {}
    )
    
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


@router.get("/summary", response_model=NetWorthSummary)
async def get_net_worth_summary(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current net worth summary with latest values"""
    user_id = UUID(current_user_id)
    
    # Get latest snapshot
    result = await session.execute(
        select(NetWorthHistory)
        .where(NetWorthHistory.user_id == user_id)
        .order_by(desc(NetWorthHistory.recorded_at))
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    
    if not latest:
        return NetWorthSummary(
            total_net_worth=0,
            total_assets=0,
            total_liabilities=0,
            change_today=0,
            change_percent=0,
            last_updated=None
        )
    
    # Get previous day's snapshot for change calculation
    prev_result = await session.execute(
        select(NetWorthHistory)
        .where(NetWorthHistory.user_id == user_id)
        .order_by(desc(NetWorthHistory.recorded_at))
        .offset(1)
        .limit(1)
    )
    previous = prev_result.scalar_one_or_none()
    
    change_today = 0
    change_percent = 0
    if previous and previous.total_net_worth > 0:
        change_today = latest.total_net_worth - previous.total_net_worth
        change_percent = (change_today / previous.total_net_worth) * 100
    
    return NetWorthSummary(
        total_net_worth=latest.total_net_worth,
        total_assets=latest.total_assets,
        total_liabilities=latest.total_liabilities,
        change_today=change_today,
        change_percent=change_percent,
        last_updated=latest.recorded_at
    )


@router.get("/goals", response_model=Optional[NetWorthGoalResponse])
async def get_goal(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's net worth goal (one per user)"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(NetWorthGoal).where(NetWorthGoal.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("/goals", response_model=NetWorthGoalResponse)
async def create_or_update_goal(
    goal_data: NetWorthGoalCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create or update net worth goal"""
    user_id = UUID(current_user_id)
    
    # Check for existing goal
    result = await session.execute(
        select(NetWorthGoal).where(NetWorthGoal.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.target_amount = goal_data.target_amount
        existing.target_date = goal_data.target_date
        existing.notify_on_progress = goal_data.notify_on_progress
        existing.notify_threshold_percent = goal_data.notify_threshold_percent
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        # Create new
        goal = NetWorthGoal(
            user_id=user_id,
            target_amount=goal_data.target_amount,
            target_date=goal_data.target_date,
            notify_on_progress=goal_data.notify_on_progress,
            notify_threshold_percent=goal_data.notify_threshold_percent
        )
        session.add(goal)
        await session.commit()
        await session.refresh(goal)
        return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a net worth goal"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(NetWorthGoal).where(
            NetWorthGoal.id == goal_id,
            NetWorthGoal.user_id == user_id
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    await session.delete(goal)
    await session.commit()
