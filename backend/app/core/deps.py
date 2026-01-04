"""Dependencies for FastAPI endpoints"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer

from app.infrastructure.db import get_db, AsyncSession
from app.services.watchlist_service import WatchlistService
from app.services.auth_service import AuthService
from app.core.config import settings


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# HTTP Bearer for backward compatibility
security = HTTPBearer(auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Get current user from JWT token.
    
    Supports both OAuth2 bearer token and HTTPBearer authentication.
    Returns user_id as string.
    """
    # Get token from either source
    auth_token = token
    if not auth_token and credentials:
        auth_token = credentials.credentials
    
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    token_payload = AuthService.verify_token(auth_token)
    
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_payload.sub


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str | None:
    """
    Get current user from JWT token, returns None if not authenticated.
    Useful for endpoints that work with or without authentication.
    """
    try:
        return await get_current_user(token, credentials)
    except HTTPException:
        return None


async def get_watchlist_service(
    session: AsyncSession = Depends(get_db)
) -> WatchlistService:
    """Dependency to get watchlist service instance"""
    return WatchlistService(session)
