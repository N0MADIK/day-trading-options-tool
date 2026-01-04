"""User model for authentication with UUID support"""
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Text, Date, Uuid
from sqlalchemy.sql import func
from app.infrastructure.db import Base


class User(Base):
    """User model for authentication - compatible with finance-flow frontend"""
    __tablename__ = 'users'
    
    # UUID primary key for compatibility with Supabase-style IDs
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Core auth fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile fields (from finance-flow schema)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    subscription_tier = Column(String(50), default='free')  # free, premium
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

