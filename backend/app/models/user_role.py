"""User Role model for role-based access control"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base


class UserRole(Base):
    """User role model for RBAC - compatible with finance-flow"""
    __tablename__ = 'user_roles'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(50), nullable=False, default='user')  # admin, user, premium
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure unique user-role combination
    __table_args__ = (
        UniqueConstraint('user_id', 'role', name='uq_user_role'),
    )
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role={self.role})>"
