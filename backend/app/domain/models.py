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


class StrategyExecution(Base):
    """Strategy execution record"""
    __tablename__ = "strategy_executions"
    
    id = Column(String(36), primary_key=True)  # UUID string
    strategy_id = Column(Integer, ForeignKey("custom_strategies.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)  # RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    output = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)  # JSON string
    trades_generated = Column(Integer, default=0)
    signals_generated = Column(Integer, default=0)
    dry_run = Column(Boolean, default=False)
    
    # Relationships
    strategy = relationship("CustomStrategy")
    
    def __repr__(self):
        return f"<StrategyExecution(id={self.id}, strategy_id={self.strategy_id}, status={self.status})>"


class StrategySignal(Base):
    """Signal generated by a strategy"""
    __tablename__ = "strategy_signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("custom_strategies.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    signal_metadata = Column(Text, nullable=True)  # JSON string
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("CustomStrategy")
    
    def __repr__(self):
        return f"<StrategySignal(id={self.id}, symbol={self.symbol}, action={self.action})>"


class StrategyPerformance(Base):
    """Strategy performance metrics"""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("custom_strategies.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    total_trades_generated = Column(Integer, default=0)
    total_signals_generated = Column(Integer, default=0)
    avg_execution_time_seconds = Column(Float, default=0.0)
    last_execution_at = Column(DateTime, nullable=True)
    profitability_metrics = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("CustomStrategy")
    
    def __repr__(self):
        return f"<StrategyPerformance(strategy_id={self.strategy_id}, success_rate={self.successful_executions}/{self.total_executions})>"


class StrategyTemplate(Base):
    """Reusable strategy template"""
    __tablename__ = "strategy_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    code_template = Column(Text, nullable=False)
    default_parameters = Column(Text, nullable=True)  # JSON string
    required_parameters = Column(Text, nullable=True)  # JSON array
    optional_parameters = Column(Text, nullable=True)  # JSON array
    tags = Column(Text, nullable=True)  # JSON array
    is_public = Column(Boolean, default=False)
    version = Column(String(20), default="1.0.0")
    usage_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    created_by = Column(String(100), nullable=True)  # User ID or "system"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<StrategyTemplate(name={self.name}, category={self.category})>"


class StrategyBacktest(Base):
    """Strategy backtest result"""
    __tablename__ = "strategy_backtests"
    
    id = Column(String(36), primary_key=True)  # UUID string (backtest_id)
    strategy_id = Column(Integer, ForeignKey("custom_strategies.id", ondelete="SET NULL"), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    win_rate = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    performance_metrics = Column(Text, nullable=True)  # JSON string
    trade_history = Column(Text, nullable=True)  # JSON string
    equity_curve = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("CustomStrategy")
    
    def __repr__(self):
        return f"<StrategyBacktest(id={self.id}, return={self.total_return})>"
