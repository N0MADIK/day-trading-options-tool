"""Database models for external service integrations"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base
import enum


class IntegrationType(enum.Enum):
    """Types of external integrations"""
    PLAID = "plaid"
    ALPACA = "alpaca"
    SNAPTRADE = "snaptrade"


class IntegrationStatus(enum.Enum):
    """Status of integration connections"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    EXPIRED = "expired"


class UserIntegration(Base):
    """User integration credentials and settings"""
    __tablename__ = 'user_integrations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    integration_type = Column(Enum(IntegrationType), nullable=False)
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.INACTIVE)
    
    # Encrypted credentials storage
    encrypted_credentials = Column(Text, nullable=False)  # JSON encrypted credentials
    
    # Integration-specific identifiers
    external_user_id = Column(String)  # e.g., Plaid item_id, SnapTrade user_id
    
    # Configuration
    is_sandbox = Column(Boolean, default=True)  # For testing vs production
    webhook_url = Column(String)
    
    # Metadata
    last_sync_at = Column(DateTime(timezone=True))
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    connected_accounts = relationship("ConnectedAccount", back_populates="integration", cascade="all, delete-orphan")


class ConnectedAccount(Base):
    """Connected external accounts through integrations"""
    __tablename__ = 'connected_accounts'
    
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey('user_integrations.id'), nullable=False)
    
    # Account identifiers
    external_account_id = Column(String, nullable=False)  # External service's account ID
    account_name = Column(String)
    account_type = Column(String)  # checking, savings, investment, etc.
    account_subtype = Column(String)
    
    # Institution info (for Plaid/SnapTrade)
    institution_name = Column(String)
    institution_id = Column(String)
    
    # Account details
    currency = Column(String, default='USD')
    available_balance = Column(String)  # Encrypted
    current_balance = Column(String)  # Encrypted
    
    # Status
    is_active = Column(Boolean, default=True)
    sync_enabled = Column(Boolean, default=True)
    last_successful_sync = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    integration = relationship("UserIntegration", back_populates="connected_accounts")
