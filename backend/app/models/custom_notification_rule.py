"""Custom Notification Rule model"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Uuid, JSON, Numeric, Time, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base


class CustomNotificationRule(Base):
    """Custom notification rule model"""
    __tablename__ = 'custom_notification_rules'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Condition configuration using JSON
    # { "metric": "price", "operator": "gt", "value": 100, "symbol": "AAPL" }
    conditions = Column(JSON, nullable=False)  # Rule conditions as JSON
    
    frequency = Column(String(50), default='immediate')  # immediate, daily, weekly
    urgency_level = Column(String(50), default='normal')  # low, normal, high, critical
    
    is_enabled = Column(Boolean, default=True)
    sensitivity = Column(Numeric(3, 1), default=5.0)  # 0-10 scale
    
    quiet_hours_start = Column(Time, nullable=True)
    quiet_hours_end = Column(Time, nullable=True)
    
    notify_email = Column(Boolean, default=True)
    notify_push = Column(Boolean, default=False)
    notify_sms = Column(Boolean, default=False)
    
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CustomNotificationRule(user_id={self.user_id}, name={self.name})>"
