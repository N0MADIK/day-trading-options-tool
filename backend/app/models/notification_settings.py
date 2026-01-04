"""Notification Settings model"""
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Uuid
from sqlalchemy.sql import func
from app.infrastructure.db import Base


class NotificationSettings(Base):
    """User notification settings - compatible with finance-flow frontend"""
    __tablename__ = 'notification_settings'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=False)
    price_alerts = Column(Boolean, default=True)
    goal_progress_alerts = Column(Boolean, default=True)
    weekly_reports = Column(Boolean, default=True)
    daily_summary = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationSettings(user_id={self.user_id})>"
