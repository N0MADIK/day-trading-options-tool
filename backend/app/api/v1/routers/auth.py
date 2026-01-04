"""Authentication API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import get_db
from app.schemas.auth import UserCreate, UserResponse, Token, UserLogin
from app.services.auth_service import AuthService
from app.core.deps import get_current_user


router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get auth service instance"""
    return AuthService(session)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    """
    try:
        user = await service.register_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """
    Login to get access token.
    
    Uses OAuth2 password flow - submit username (email) and password.
    """
    user = await service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = service.create_access_token(user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/token", response_model=Token)
async def login_for_token(
    credentials: UserLogin,
    service: AuthService = Depends(get_auth_service)
):
    """
    Alternative login endpoint accepting JSON body.
    """
    user = await service.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = service.create_access_token(user.id)
    return Token(access_token=access_token, token_type="bearer")



@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user_id: str = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    user = await service.get_user_by_id(current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
