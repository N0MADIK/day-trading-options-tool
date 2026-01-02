from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.services.watchlist_service import WatchlistService
from app.core.deps import get_watchlist_service
from app.schemas.watchlist import (
    TickerWatchlistCreate,
    TickerWatchlistResponse,
    TickerWatchlistList,
    OptionWatchlistCreate,
    OptionWatchlistResponse,
    OptionWatchlistList,
    WatchlistCheckResponse
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


# ========== TICKER WATCHLIST ENDPOINTS ==========

@router.get("/tickers", response_model=TickerWatchlistList)
async def get_tickers(
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Get all tickers in watchlist"""
    try:
        tickers = await service.get_all_tickers()
        return TickerWatchlistList(tickers=tickers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tickers", response_model=TickerWatchlistResponse)
async def add_ticker(
    ticker_data: TickerWatchlistCreate,
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Add a ticker to watchlist"""
    try:
        return await service.add_ticker(ticker_data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tickers/{symbol}")
async def remove_ticker(
    symbol: str,
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Remove a ticker from watchlist"""
    try:
        await service.remove_ticker(symbol)
        return {"success": True, "message": f"Ticker {symbol} removed from watchlist"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== OPTION WATCHLIST ENDPOINTS ==========

@router.get("/options", response_model=OptionWatchlistList)
async def get_options_watchlist(
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Get all options in watchlist"""
    try:
        options = await service.get_all_options()
        return OptionWatchlistList(options=options)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/options", response_model=OptionWatchlistResponse)
async def add_option(
    option_data: OptionWatchlistCreate,
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Add an option to watchlist"""
    try:
        return await service.add_option(option_data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/options/{contract_symbol}")
async def remove_option(
    contract_symbol: str,
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Remove an option from watchlist"""
    try:
        await service.remove_option(contract_symbol)
        return {"success": True, "message": f"Option {contract_symbol} removed from watchlist"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/check/{contract_symbol}", response_model=WatchlistCheckResponse)
async def check_option_in_watchlist(
    contract_symbol: str,
    service: WatchlistService = Depends(get_watchlist_service)
):
    """Check if an option is in the watchlist"""
    try:
        return await service.check_option_in_watchlist(contract_symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
