"""User Profiles API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.infrastructure.db import get_async_session
from app.services.auth_service import AuthService
from app.core.deps import get_current_user
from app.schemas.auth import UserResponse, UserProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


async def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    """Dependency to get auth service instance"""
    return AuthService(session)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user_id: str = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """Get current user's profile"""
    user = await service.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user_id: str = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """Update current user's profile"""
    user = await service.update_user_profile(current_user_id, profile_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_profile_by_id(
    user_id: UUID,
    current_user_id: str = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    """Get profile by user ID (admin only)"""
    # Import here to avoid circular import
    from app.models.user_role import UserRole
    from sqlalchemy import select
    
    # Check if current user is admin
    admin_check = await session.execute(
        select(UserRole).where(
            UserRole.user_id == UUID(current_user_id),
            UserRole.role == 'admin'
        )
    )
    is_admin = admin_check.scalar_one_or_none() is not None
    
    # Allow access if admin or viewing own profile
    if not is_admin and str(user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile"
        )
    
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
