from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class TickerWatchlistBase(BaseModel):
    """Base schema for ticker watchlist"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    category: str = Field(default="Other", description="Category classification")


class TickerWatchlistCreate(TickerWatchlistBase):
    """Schema for creating a ticker watchlist entry"""
    
    @validator('symbol')
    def normalize_symbol(cls, v):
        return v.upper().strip()


class TickerWatchlistUpdate(BaseModel):
    """Schema for updating a ticker watchlist entry"""
    category: Optional[str] = Field(None, description="Category classification")


class TickerWatchlistResponse(TickerWatchlistBase):
    """Schema for ticker watchlist response"""
    id: int
    added_at: datetime
    
    class Config:
        from_attributes = True


class OptionWatchlistBase(BaseModel):
    """Base schema for option watchlist"""
    contract_symbol: str = Field(..., description="Option contract symbol")
    ticker: str = Field(..., min_length=1, max_length=10, description="Underlying ticker")
    strike: float = Field(..., gt=0, description="Strike price")
    expiry: str = Field(..., description="Expiration date (YYYY-MM-DD)")
    option_type: str = Field(..., pattern="^(CALL|PUT)$", description="Option type")
    notes: str = Field(default="", description="Optional notes")


class OptionWatchlistCreate(OptionWatchlistBase):
    """Schema for creating an option watchlist entry"""
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()
    
    @validator('option_type')
    def normalize_option_type(cls, v):
        return v.upper()


class OptionWatchlistUpdate(BaseModel):
    """Schema for updating an option watchlist entry"""
    notes: Optional[str] = Field(None, description="Optional notes")


class OptionWatchlistResponse(OptionWatchlistBase):
    """Schema for option watchlist response"""
    id: int
    added_at: datetime
    
    class Config:
        from_attributes = True


class WatchlistCheckResponse(BaseModel):
    """Schema for checking if option is in watchlist"""
    in_watchlist: bool = Field(..., description="Whether option is in watchlist")


# Bulk operations
class TickerWatchlistList(BaseModel):
    """Schema for list of ticker watchlist entries"""
    tickers: List[TickerWatchlistResponse]


class OptionWatchlistList(BaseModel):
    """Schema for list of option watchlist entries"""
    options: List[OptionWatchlistResponse]
