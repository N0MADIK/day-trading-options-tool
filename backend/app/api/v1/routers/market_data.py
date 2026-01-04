"""Market Data API router - Stock quotes and options chains"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, date

from app.core.deps import get_current_user
from app.schemas.market_data import (
    StockQuoteRequest,
    StockQuoteResponse,
    OptionsChainRequest,
    OptionsChainResponse,
    HistoricalDataResponse,
    SymbolSearchResult
)

router = APIRouter(prefix="/market", tags=["market-data"])


@router.post("/quote", response_model=StockQuoteResponse)
async def get_stock_quote(
    request: StockQuoteRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get real-time stock quote.
    Uses Yahoo Finance by default, can use user's data subscription if available.
    """
    # Import the options service for market data
    try:
        from app.services.options_service import OptionsService
        options_service = OptionsService()
        
        # Use yfinance for basic quote
        import yfinance as yf
        ticker = yf.Ticker(request.symbol)
        info = ticker.info
        
        return StockQuoteResponse(
            symbol=request.symbol,
            price=info.get('regularMarketPrice', info.get('currentPrice', 0)),
            change=info.get('regularMarketChange', 0),
            change_percent=info.get('regularMarketChangePercent', 0),
            volume=info.get('regularMarketVolume', 0),
            market_cap=info.get('marketCap'),
            pe_ratio=info.get('trailingPE'),
            high=info.get('regularMarketDayHigh'),
            low=info.get('regularMarketDayLow'),
            open=info.get('regularMarketOpen'),
            previous_close=info.get('regularMarketPreviousClose'),
            name=info.get('shortName', request.symbol),
            timestamp=datetime.now()
        )
    except Exception as e:
        # Return mock data if yfinance fails
        return StockQuoteResponse(
            symbol=request.symbol,
            price=0,
            change=0,
            change_percent=0,
            volume=0,
            name=request.symbol,
            timestamp=datetime.now(),
            error=str(e)
        )


@router.post("/options-chain", response_model=OptionsChainResponse)
async def get_options_chain(
    request: OptionsChainRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get options chain for a symbol.
    Returns calls and puts for specified expiration.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(request.symbol)
        
        # Get available expirations
        expirations = ticker.options
        
        if not expirations:
            return OptionsChainResponse(
                symbol=request.symbol,
                expirations=[],
                calls=[],
                puts=[],
                underlying_price=0
            )
        
        # Use requested expiration or first available
        expiration = request.expiration or expirations[0]
        if expiration not in expirations:
            expiration = expirations[0]
        
        opt = ticker.option_chain(expiration)
        info = ticker.info
        
        calls = opt.calls.to_dict('records') if not opt.calls.empty else []
        puts = opt.puts.to_dict('records') if not opt.puts.empty else []
        
        return OptionsChainResponse(
            symbol=request.symbol,
            expirations=list(expirations),
            selected_expiration=expiration,
            calls=calls,
            puts=puts,
            underlying_price=info.get('regularMarketPrice', 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch options chain: {str(e)}")


@router.get("/historical/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_data(
    symbol: str,
    period: str = Query("1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query("1d", description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo"),
    current_user_id: str = Depends(get_current_user)
):
    """Get historical price data for a symbol"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        data = []
        for index, row in hist.iterrows():
            data.append({
                "date": index.isoformat(),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": int(row['Volume'])
            })
        
        return HistoricalDataResponse(
            symbol=symbol,
            period=period,
            interval=interval,
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")


@router.get("/search/{query}", response_model=List[SymbolSearchResult])
async def search_symbols(
    query: str,
    limit: int = Query(10, le=50),
    current_user_id: str = Depends(get_current_user)
):
    """Search for stock symbols by name or ticker"""
    try:
        import yfinance as yf
        # yfinance doesn't have a great search, so we'll use a basic approach
        # In production, you'd want to use a proper API like Polygon or Alpha Vantage
        
        # Try to get ticker info directly
        ticker = yf.Ticker(query.upper())
        info = ticker.info
        
        if info and info.get('shortName'):
            return [SymbolSearchResult(
                symbol=query.upper(),
                name=info.get('shortName', query),
                type=info.get('quoteType', 'EQUITY'),
                exchange=info.get('exchange', '')
            )]
        return []
    except:
        return []
