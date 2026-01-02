from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from app.infrastructure.clients.yfinance_client import YFinanceClient
from app.schemas.options import (
    StockQuoteRequest, StockQuoteResponse, QuoteLiteResponse,
    OptionsChainRequest, OptionsChainResponse, OptionContract,
    TopVolumeOptionsRequest, TopVolumeOptionsResponse,
    StockHistoryRequest, StockHistoryResponse,
    UnusualActivityRequest, UnusualActivityResponse,
    MarketScanResponse
)
from app.domain.errors import ExternalServiceError, ValidationError, NotFoundError


class OptionsService:
    """Service for options data operations"""
    
    def __init__(self):
        self.yfinance_client = YFinanceClient()
    
    async def get_stock_quote(self, request: StockQuoteRequest) -> StockQuoteResponse:
        """Get current stock quote"""
        try:
            data = await self.yfinance_client.get_stock_quote(request.ticker)
            return StockQuoteResponse(**data)
        except ExternalServiceError as e:
            raise e
        except Exception as e:
            raise ExternalServiceError(f"Failed to get stock quote for {request.ticker}", "yfinance", {"error": str(e)})
    
    async def get_quote_lite(self, request: StockQuoteRequest) -> QuoteLiteResponse:
        """Get lightweight quote for live updates"""
        try:
            data = await self.yfinance_client.get_quote_lite(request.ticker)
            return QuoteLiteResponse(**data)
        except ExternalServiceError as e:
            raise e
        except Exception as e:
            raise ExternalServiceError(f"Failed to get lite quote for {request.ticker}", "yfinance", {"error": str(e)})
    
    async def get_options_chain(self, request: OptionsChainRequest) -> OptionsChainResponse:
        """Get options chain for a stock"""
        try:
            data = await self.yfinance_client.get_options_chain(request.ticker, request.expiry)
            
            # Convert to response format
            calls = [OptionContract(**call) for call in data.get("calls", [])]
            puts = [OptionContract(**put) for put in data.get("puts", [])]
            
            return OptionsChainResponse(
                ticker=data["ticker"],
                expiry=data.get("expiry"),
                calls=calls,
                puts=puts
            )
        except ExternalServiceError as e:
            raise e
        except Exception as e:
            raise ExternalServiceError(f"Failed to get options chain for {request.ticker}", "yfinance", {"error": str(e)})
    
    async def get_top_volume_options(self, request: TopVolumeOptionsRequest) -> TopVolumeOptionsResponse:
        """Get top volume options for near-term expiry"""
        try:
            # Get options chain
            chain_request = OptionsChainRequest(ticker=request.ticker)
            chain_response = await self.get_options_chain(chain_request)
            
            # Combine calls and puts
            all_options = chain_response.calls + chain_response.puts
            
            # Filter by volume and sort
            options_with_volume = [
                opt for opt in all_options 
                if opt.volume and opt.volume > 0
            ]
            
            # Sort by volume (descending)
            options_with_volume.sort(key=lambda x: x.volume, reverse=True)
            
            # Take top N
            top_options = options_with_volume[:request.top_n]
            
            return TopVolumeOptionsResponse(
                ticker=request.ticker,
                options=top_options
            )
        except Exception as e:
            raise ExternalServiceError(f"Failed to get top volume options for {request.ticker}", "yfinance", {"error": str(e)})
    
    async def get_stock_history(self, request: StockHistoryRequest) -> StockHistoryResponse:
        """Get stock price history with technical indicators"""
        try:
            data = await self.yfinance_client.get_stock_history(
                request.ticker, request.period, request.interval
            )
            
            return StockHistoryResponse(**data)
        except ExternalServiceError as e:
            raise e
        except Exception as e:
            raise ExternalServiceError(f"Failed to get stock history for {request.ticker}", "yfinance", {"error": str(e)})
    
    async def get_option_history(self, contract_symbol: str, period: str = "1mo", interval: str = "1d"):
        """Get historical price data for a specific option contract"""
        try:
            # Parse contract symbol to get ticker and expiry
            # Format: AAPL240119C00150000
            if len(contract_symbol) < 15:
                raise ValidationError(f"Invalid contract symbol format: {contract_symbol}")
            
            ticker = contract_symbol[:6].rstrip()
            expiry_str = contract_symbol[6:12]
            option_type = "CALL" if contract_symbol[12] == "C" else "PUT"
            
            # Convert expiry to YYYY-MM-DD
            expiry_date = f"20{expiry_str[:2]}-{expiry_str[2:4]}-{expiry_str[4:6]}"
            
            # Get historical data for the underlying stock
            history_request = StockHistoryRequest(
                ticker=ticker,
                period=period,
                interval=interval
            )
            history_response = await self.get_stock_history(history_request)
            
            return {
                "contract_symbol": contract_symbol,
                "ticker": ticker,
                "expiry": expiry_date,
                "option_type": option_type,
                "period": period,
                "interval": interval,
                "prices": history_response.prices,
                "note": "Option historical data approximated using underlying stock prices"
            }
        except Exception as e:
            raise ExternalServiceError(f"Failed to get option history for {contract_symbol}", "yfinance", {"error": str(e)})
    
    async def detect_unusual_activity(self, request: UnusualActivityRequest) -> UnusualActivityResponse:
        """Detect unusual options activity"""
        try:
            # Get options chain
            chain_request = OptionsChainRequest(ticker=request.ticker)
            chain_response = await self.get_options_chain(chain_request)
            
            # Analyze for unusual activity
            unusual_options = []
            
            for option in chain_response.calls + chain_response.puts:
                # Define unusual activity criteria
                volume_oi_ratio = 0
                if option.open_interest and option.open_interest > 0:
                    volume_oi_ratio = option.volume / option.open_interest if option.volume else 0
                
                # High volume relative to open interest
                if volume_oi_ratio > 0.5:  # Volume > 50% of open interest
                    unusual_options.append({
                        "contract": option.dict(),
                        "reason": "High volume/interest ratio",
                        "volume_oi_ratio": volume_oi_ratio
                    })
                
                # High implied volatility
                if option.implied_volatility and option.implied_volatility > 1.0:  # > 100%
                    unusual_options.append({
                        "contract": option.dict(),
                        "reason": "High implied volatility",
                        "implied_volatility": option.implied_volatility
                    })
                
                # Large bid-ask spread (could indicate illiquidity or unusual activity)
                if option.bid and option.ask:
                    spread_pct = (option.ask - option.bid) / option.ask * 100
                    if spread_pct > 20:  # > 20% spread
                        unusual_options.append({
                            "contract": option.dict(),
                            "reason": "Wide bid-ask spread",
                            "spread_pct": spread_pct
                        })
            
            # Sort by significance (you could implement a scoring system)
            unusual_options.sort(key=lambda x: x.get("volume_oi_ratio", 0), reverse=True)
            
            analysis = f"Found {len(unusual_options)} contracts with unusual activity"
            if unusual_options:
                top_reason = unusual_options[0].get("reason", "Unknown")
                analysis += f". Top reason: {top_reason}"
            
            return UnusualActivityResponse(
                ticker=request.ticker,
                unusual_options=unusual_options[:10],  # Limit to top 10
                analysis=analysis
            )
        except Exception as e:
            raise ExternalServiceError(f"Failed to detect unusual activity for {request.ticker}", "yfinance", {"error": str(e)})
    
    async def market_scan(self, tickers: List[str]) -> MarketScanResponse:
        """Scan market for most active options across multiple tickers"""
        try:
            scan_results = []
            
            # Process tickers concurrently
            tasks = []
            for ticker in tickers:
                task = self._scan_single_ticker(ticker)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                ticker = tickers[i]
                if isinstance(result, Exception):
                    scan_results.append({
                        "ticker": ticker,
                        "error": str(result)
                    })
                else:
                    scan_results.append(result)
            
            return MarketScanResponse(scan_results=scan_results)
        except Exception as e:
            raise ExternalServiceError("Failed to perform market scan", "yfinance", {"error": str(e)})
    
    async def _scan_single_ticker(self, ticker: str) -> Dict[str, Any]:
        """Scan a single ticker for active options"""
        try:
            # Get top volume options
            top_request = TopVolumeOptionsRequest(ticker=ticker, top_n=5)
            top_response = await self.get_top_volume_options(top_request)
            
            # Get current quote
            quote_request = StockQuoteRequest(ticker=ticker)
            quote_response = await self.get_stock_quote(quote_request)
            
            # Calculate total volume
            total_volume = sum(opt.volume or 0 for opt in top_response.options)
            
            return {
                "ticker": ticker,
                "stock_price": quote_response.price,
                "change": quote_response.change,
                "change_percent": quote_response.change_percent,
                "total_options_volume": total_volume,
                "top_options": [opt.dict() for opt in top_response.options],
                "scan_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "ticker": ticker,
                "error": str(e)
            }
    
    async def close(self):
        """Close the service and cleanup resources"""
        await self.yfinance_client.close()
