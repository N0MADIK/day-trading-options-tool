"""User Roles API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.infrastructure.db import get_async_session
from app.models.user_role import UserRole
from app.core.deps import get_current_user
from app.schemas.user_role import (
    UserRoleResponse,
    UserRoleCreate,
    RoleCheckResponse
)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/me", response_model=List[UserRoleResponse])
async def get_my_roles(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all roles for the current user"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(UserRole).where(UserRole.user_id == user_id)
    )
    return result.scalars().all()


@router.get("/check/{role}", response_model=RoleCheckResponse)
async def check_role(
    role: str,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Check if current user has a specific role (replaces Supabase has_role RPC)"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role == role
        )
    )
    exists = result.scalar_one_or_none() is not None
    return RoleCheckResponse(has_role=exists, role=role)


@router.post("/", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def assign_role(
    role_data: UserRoleCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Assign a role to a user (admin only)"""
    # Check if current user is admin
    admin_check = await session.execute(
        select(UserRole).where(
            UserRole.user_id == UUID(current_user_id),
            UserRole.role == 'admin'
        )
    )
    if not admin_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign roles"
        )
    
    # Check if role already exists
    existing = await session.execute(
        select(UserRole).where(
            UserRole.user_id == role_data.user_id,
            UserRole.role == role_data.role
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has role: {role_data.role}"
        )
    
    # Create new role
    user_role = UserRole(
        user_id=role_data.user_id,
        role=role_data.role
    )
    session.add(user_role)
    await session.commit()
    await session.refresh(user_role)
    return user_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role(
    role_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove a role (admin only)"""
    # Check if current user is admin
    admin_check = await session.execute(
        select(UserRole).where(
            UserRole.user_id == UUID(current_user_id),
            UserRole.role == 'admin'
        )
    )
    if not admin_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can remove roles"
        )
    
    # Find and delete the role
    result = await session.execute(
        select(UserRole).where(UserRole.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    await session.delete(role)
    await session.commit()
