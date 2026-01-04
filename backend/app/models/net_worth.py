"""Net Worth models for tracking history and goals"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Uuid, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base


class NetWorthHistory(Base):
    """Net Worth history model"""
    __tablename__ = 'net_worth_history'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    total_net_worth = Column(Float, nullable=False)
    cash_balance = Column(Float, default=0)
    assets_balance = Column(Float, default=0)
    liabilities_balance = Column(Float, default=0)
    
    # Store breakdown of assets/liabilities as JSON
    # { "accounts": [...], "assets": [...] }
    breakdown = Column(JSON, nullable=True)
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NetWorthHistory(user_id={self.user_id}, value={self.total_net_worth})>"


class NetWorthGoal(Base):
    """Net worth goals - one per user"""
    __tablename__ = 'net_worth_goals'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    target_amount = Column(Numeric(15, 2), nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=True)
    
    notify_on_progress = Column(Boolean, default=True)
    notify_threshold_percent = Column(Numeric(5, 2), default=5.00)  # Notify when % milestone reached
    
    last_notified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NetWorthGoal(user_id={self.user_id}, target={self.target_amount})>"
