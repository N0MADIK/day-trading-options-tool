"""Personal Finance models for aggregation and tracking"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, Uuid, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.db import Base
from app.schemas.personal_finance import (
    SourceType, ConnectionStatus, AccountType, AccountSubtype, 
    SecurityType, TransactionType, SyncMode, SyncStatus
)

class Institution(Base):
    """Financial institution model"""
    __tablename__ = 'institutions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    brand_key = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # stored as string for flexibility
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    connections = relationship("Connection", back_populates="institution")
    
    def __repr__(self):
        return f"<Institution(name={self.name}, brand_key={self.brand_key})>"


class Connection(Base):
    """User connection to an institution"""
    __tablename__ = 'connections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False)
    
    source_type = Column(String(50), nullable=False)
    status = Column(String(50), default=ConnectionStatus.ACTIVE.value)
    
    # Authentication data (encrypted)
    auth_blob_encrypted = Column(Text, nullable=True)
    
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    next_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error_code = Column(String(50), nullable=True)
    last_error_message = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    institution = relationship("Institution", back_populates="connections")
    accounts = relationship("Account", back_populates="connection", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="connection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Connection(user_id={self.user_id}, institution_id={self.institution_id})>"


class Account(Base):
    """Financial account model"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey('connections.id', ondelete='CASCADE'), nullable=False, index=True)
    external_account_id = Column(String(100), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False)
    account_subtype = Column(String(50), nullable=True)
    currency = Column(String(3), default='USD')
    institution_masked_number = Column(String(50), nullable=True)
    is_closed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    connection = relationship("Connection", back_populates="accounts")
    holdings = relationship("Holding", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(name={self.name}, type={self.account_type})>"


class Security(Base):
    """Security model (Stock, ETF, etc.)"""
    __tablename__ = 'securities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    cusip = Column(String(20), nullable=True)
    isin = Column(String(20), nullable=True)
    security_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    holdings = relationship("Holding", back_populates="security")
    transactions = relationship("Transaction", back_populates="security")
    
    def __repr__(self):
        return f"<Security(symbol={self.symbol}, name={self.name})>"


class Holding(Base):
    """Account holding model"""
    __tablename__ = 'holdings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    security_id = Column(Integer, ForeignKey('securities.id', ondelete='CASCADE'), nullable=False, index=True)
    
    quantity = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    as_of_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="holdings")
    security = relationship("Security", back_populates="holdings")
    
    def __repr__(self):
        return f"<Holding(account_id={self.account_id}, security_id={self.security_id})>"


class Transaction(Base):
    """Financial transaction model"""
    __tablename__ = 'transactions_pf'  # suffix to avoid conflict with Trade (options tool) if needed, but safer
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    security_id = Column(Integer, ForeignKey('securities.id'), nullable=True)
    
    external_transaction_id = Column(String(100), nullable=True, index=True)
    transaction_type = Column(String(50), nullable=False)
    
    quantity = Column(Float, nullable=True)
    amount = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    currency = Column(String(3), default='USD')
    
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    settle_date = Column(DateTime(timezone=True), nullable=True)
    
    description = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    raw_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    security = relationship("Security", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.transaction_type})>"


class SyncJob(Base):
    """Synchronization job history"""
    __tablename__ = 'sync_jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey('connections.id', ondelete='CASCADE'), nullable=False, index=True)
    
    sync_mode = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    records_processed = Column(Integer, default=0)
    records_success = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    error_message = Column(String(1000), nullable=True)
    output = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    connection = relationship("Connection", back_populates="sync_jobs")
    
    def __repr__(self):
        return f"<SyncJob(connection_id={self.connection_id}, status={self.status})>"
