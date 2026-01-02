from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

from app.infrastructure.db import Base


class TickerWatchlist(Base):
    """Ticker watchlist model for market scanning"""
    __tablename__ = "ticker_watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    category = Column(String(50), default="Other")
    added_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TickerWatchlist(symbol={self.symbol}, category={self.category})>"


class OptionWatchlist(Base):
    """Option contract watchlist model for tracking"""
    __tablename__ = "option_watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_symbol = Column(String(50), unique=True, nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    strike = Column(Float, nullable=False)
    expiry = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    option_type = Column(String(4), nullable=False)  # 'CALL' or 'PUT'
    notes = Column(Text, default="")
    added_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OptionWatchlist(contract={self.contract_symbol}, ticker={self.ticker})>"


class Strategy(Base):
    """Trading strategy configuration"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    scan_criteria = Column(Text)  # JSON string
    default_stop_loss_pct = Column(Float)
    default_take_profit_pct = Column(Float)
    notifications_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trades = relationship("Trade", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name={self.name})>"


class Trade(Base):
    """Trade tracking model"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    contract_symbol = Column(String(50), nullable=False)
    ticker = Column(String(10), nullable=False)
    entry_date = Column(DateTime, default=datetime.utcnow)
    entry_price = Column(Float, nullable=False)
    fill_price = Column(Float)
    quantity = Column(Integer, default=1)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, CANCELLED
    exit_date = Column(DateTime)
    exit_price = Column(Float)
    pnl = Column(Float)
    notifications_enabled = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(id={self.id}, contract={self.contract_symbol}, status={self.status})>"


class CustomStrategy(Base):
    """Custom strategy script model"""
    __tablename__ = "custom_strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(Text)
    schedule_type = Column(String(20), default="INTERVAL")  # INTERVAL, CRON
    schedule_value = Column(String(50), default="60")  # seconds or cron expression
    execution_type = Column(String(20), default="HOST")  # HOST, DOCKER
    is_active = Column(Boolean, default=False)
    targets = Column(Text)  # JSON string of target symbols
    last_run = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    logs = relationship("StrategyLog", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomStrategy(id={self.id}, name={self.name}, active={self.is_active})>"


class StrategyLog(Base):
    """Strategy execution log"""
    __tablename__ = "strategy_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("custom_strategies.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # SUCCESS, ERROR, TIMEOUT
    output = Column(Text)
    trades_generated = Column(Integer, default=0)
    
    # Relationships
    strategy = relationship("CustomStrategy", back_populates="logs")
    
    def __repr__(self):
        return f"<StrategyLog(id={self.id}, strategy_id={self.strategy_id}, status={self.status})>"
