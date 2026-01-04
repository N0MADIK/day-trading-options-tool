"""User Role schemas for request/response validation"""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class UserRoleCreate(BaseModel):
    """Schema for assigning a role to a user"""
    user_id: UUID
    role: str  # admin, user, premium


class UserRoleResponse(BaseModel):
    """Schema for role response"""
    id: UUID
    user_id: UUID
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleCheckResponse(BaseModel):
    """Schema for role check response (replaces Supabase has_role RPC)"""
    has_role: bool
    role: str
