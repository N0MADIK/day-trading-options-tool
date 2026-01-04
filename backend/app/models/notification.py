"""Notification models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Uuid, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base

class Notification(Base):
    """Notification model"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default='normal')
    channel = Column(String(20), default='in_app')
    
    data = Column(JSON, nullable=True)
    read = Column(Boolean, default=False)
    status = Column(String(20), default='pending')
    
    expires_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title={self.title})>"


class NotificationTemplate(Base):
    """Notification template model"""
    __tablename__ = 'notification_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    
    default_priority = Column(String(20), default='normal')
    default_channel = Column(String(20), default='in_app')
    
    variables = Column(JSON, default=list)  # List of variable names
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationTemplate(name={self.name})>"


class NotificationDigest(Base):
    """Notification digest for batch delivery"""
    __tablename__ = 'notification_digests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    frequency = Column(String(20), nullable=False)  # daily, weekly
    channel = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    content = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationDigest(user_id={self.user_id}, frequency={self.frequency})>"
