"""Authentication service for user management and JWT tokens - UUID compatible"""
from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import UserCreate, Token, TokenPayload, UserProfileUpdate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.domain.errors import ValidationError, NotFoundError, ConflictError


class AuthService:
    """Service for authentication and user management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        result = await self.session.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ConflictError(f"User with email {user_data.email} already exists")
        
        # Create new user with hashed password and optional profile fields
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise ValidationError("User account is inactive")
        
        return user
    
    async def get_user_by_id(self, user_id: Union[UUID, str]) -> Optional[User]:
        """Get user by UUID"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None
        
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_user_profile(self, user_id: Union[UUID, str], profile_data: UserProfileUpdate) -> Optional[User]:
        """Update user profile fields"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    def create_access_token(self, user_id: Union[UUID, str], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            return TokenPayload(sub=payload.get("sub"), exp=payload.get("exp"))
        except JWTError:
            return None
