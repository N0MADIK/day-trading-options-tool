from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.services.options_service import OptionsService
from app.schemas.options import (
    StockQuoteRequest, StockQuoteResponse, QuoteLiteResponse,
    OptionsChainRequest, OptionsChainResponse,
    TopVolumeOptionsRequest, TopVolumeOptionsResponse,
    StockHistoryRequest, StockHistoryResponse,
    UnusualActivityRequest, UnusualActivityResponse,
    MarketScanResponse, OptionHistoryRequest, OptionHistoryResponse
)
from app.domain.errors import ExternalServiceError, ValidationError, NotFoundError

router = APIRouter(prefix="/options", tags=["options"])

# Dependency for options service
async def get_options_service() -> OptionsService:
    """Get options service instance"""
    return OptionsService()


@router.get("/quote/{ticker}", response_model=StockQuoteResponse)
async def get_stock_quote(
    ticker: str,
    service: OptionsService = Depends(get_options_service)
):
    """Get current stock quote"""
    try:
        request = StockQuoteRequest(ticker=ticker)
        return await service.get_stock_quote(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote-lite/{ticker}", response_model=QuoteLiteResponse)
async def get_quote_lite(
    ticker: str,
    service: OptionsService = Depends(get_options_service)
):
    """Lightweight quote for live updates - fast price data only"""
    try:
        request = StockQuoteRequest(ticker=ticker)
        return await service.get_quote_lite(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/{ticker}", response_model=OptionsChainResponse)
async def get_options_chain(
    ticker: str,
    expiry: Optional[str] = Query(None, description="Expiration date (YYYY-MM-DD)"),
    service: OptionsService = Depends(get_options_service)
):
    """Get options chain for a stock"""
    try:
        request = OptionsChainRequest(ticker=ticker, expiry=expiry)
        return await service.get_options_chain(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-volume/{ticker}", response_model=TopVolumeOptionsResponse)
async def get_top_volume_options(
    ticker: str,
    top_n: int = Query(10, ge=1, le=50, description="Number of top options to return"),
    service: OptionsService = Depends(get_options_service)
):
    """Get top volume options for near-term expiry (1-2 days out)"""
    try:
        request = TopVolumeOptionsRequest(ticker=ticker, top_n=top_n)
        return await service.get_top_volume_options(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{ticker}", response_model=StockHistoryResponse)
async def get_stock_history(
    ticker: str,
    period: str = Query("3mo", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    interval: str = Query("1d", description="Interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)"),
    service: OptionsService = Depends(get_options_service)
):
    """Get stock price history with EMAs and technical indicators"""
    try:
        request = StockHistoryRequest(ticker=ticker, period=period, interval=interval)
        return await service.get_stock_history(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unusual/{ticker}", response_model=UnusualActivityResponse)
async def detect_unusual_activity(
    ticker: str,
    service: OptionsService = Depends(get_options_service)
):
    """Detect unusual options activity"""
    try:
        request = UnusualActivityRequest(ticker=ticker)
        return await service.detect_unusual_activity(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/option-history/{contract_symbol}", response_model=OptionHistoryResponse)
async def get_option_history(
    contract_symbol: str,
    period: str = Query("1mo", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    interval: str = Query("1d", description="Interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)"),
    service: OptionsService = Depends(get_options_service)
):
    """Get historical prices for a specific option contract"""
    try:
        result = await service.get_option_history(contract_symbol, period, interval)
        return OptionHistoryResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan", response_model=MarketScanResponse)
async def market_scan(
    service: OptionsService = Depends(get_options_service)
):
    """Scan top stocks for most active options - uses watchlist tickers"""
    try:
        # For now, use a default list of popular tickers
        # In a real implementation, this would come from the watchlist service
        default_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
            "SPY", "QQQ", "IWM", "AMD", "NFLX", "CRM", "ORCL"
        ]
        
        return await service.market_scan(default_tickers)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
