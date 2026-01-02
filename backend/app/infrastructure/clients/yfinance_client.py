import yfinance as yf
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import math
from scipy.stats import norm
import time
from functools import lru_cache

from app.domain.errors import ExternalServiceError, ValidationError


class YFinanceClient:
    """Client for yfinance external API with async support"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_stock_quote(self, ticker: str) -> Dict[str, Any]:
        """Get current stock quote asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, self._get_stock_quote_sync, ticker
            )
            return result
        except Exception as e:
            raise ExternalServiceError(f"Failed to fetch quote for {ticker}", "yfinance", {"error": str(e)})
    
    def _get_stock_quote_sync(self, ticker: str) -> Dict[str, Any]:
        """Synchronous stock quote fetch"""
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Handle missing data
        if not info or 'regularMarketPrice' not in info:
            # Try to get from historical data
            hist = stock.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            else:
                raise ExternalServiceError(f"No data available for {ticker}", "yfinance")
        else:
            current_price = info.get('regularMarketPrice', 0)
            prev_close = info.get('regularMarketPreviousClose', current_price)
            change = info.get('regularMarketChange', current_price - prev_close)
            change_pct = info.get('regularMarketChangePercent', (change / prev_close * 100) if prev_close > 0 else 0)
        
        return {
            "ticker": ticker.upper(),
            "price": current_price,
            "change": change,
            "change_percent": change_pct,
            "volume": info.get('regularMarketVolume'),
            "market_cap": info.get('marketCap'),
            "day_high": info.get('dayHigh'),
            "day_low": info.get('dayLow'),
            "year_high": info.get('fiftyTwoWeekHigh'),
            "year_low": info.get('fiftyTwoWeekLow'),
        }
    
    async def get_quote_lite(self, ticker: str) -> Dict[str, Any]:
        """Get lightweight quote for live updates"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, self._get_quote_lite_sync, ticker
            )
            return result
        except Exception as e:
            raise ExternalServiceError(f"Failed to fetch lite quote for {ticker}", "yfinance", {"error": str(e)})
    
    def _get_quote_lite_sync(self, ticker: str) -> Dict[str, Any]:
        """Synchronous lightweight quote fetch"""
        stock = yf.Ticker(ticker)
        
        # Use fast_info for speed
        try:
            fast_info = stock.fast_info
            current_price = fast_info.get('last_price')
            if not current_price:
                # Fallback to regular info
                info = stock.info
                current_price = info.get('regularMarketPrice', 0)
            
            # Get previous close for change calculation
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            else:
                change = 0
                change_pct = 0
            
            return {
                "ticker": ticker.upper(),
                "price": current_price,
                "change": change,
                "change_percent": change_pct,
            }
        except Exception as e:
            raise ExternalServiceError(f"Failed to fetch lite quote for {ticker}", "yfinance", {"error": str(e)})
    
    async def get_options_chain(self, ticker: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        """Get options chain asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, self._get_options_chain_sync, ticker, expiry
            )
            return result
        except Exception as e:
            raise ExternalServiceError(f"Failed to fetch options chain for {ticker}", "yfinance", {"error": str(e)})
    
    def _get_options_chain_sync(self, ticker: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous options chain fetch"""
        stock = yf.Ticker(ticker)
        
        # Get available expiries if not specified
        try:
            expiries = stock.options
            if not expiries:
                return {"ticker": ticker.upper(), "error": "No options data available"}
            
            if expiry:
                if expiry not in expiries:
                    # Find closest expiry
                    expiry_dates = [datetime.strptime(exp, "%Y-%m-%d") for exp in expiries]
                    target_date = datetime.strptime(expiry, "%Y-%m-%d")
                    closest_expiry = min(expiry_dates, key=lambda x: abs((x - target_date).days))
                    expiry = closest_expiry.strftime("%Y-%m-%d")
            else:
                # Use nearest expiry (> 7 days from now)
                today = datetime.now()
                expiry_dates = [datetime.strptime(exp, "%Y-%m-%d") for exp in expiries]
                future_dates = [d for d in expiry_dates if d > today + timedelta(days=7)]
                if future_dates:
                    expiry = min(future_dates).strftime("%Y-%m-%d")
                else:
                    expiry = expiries[0]  # Fallback to first available
            
            # Get options data
            opt = stock.option_chain(expiry)
            
            # Process calls and puts
            calls = []
            puts = []
            
            for _, row in opt.calls.iterrows():
                calls.append(self._process_option_row(row, "CALL", expiry, ticker))
            
            for _, row in opt.puts.iterrows():
                puts.append(self._process_option_row(row, "PUT", expiry, ticker))
            
            return {
                "ticker": ticker.upper(),
                "expiry": expiry,
                "calls": calls,
                "puts": puts
            }
            
        except Exception as e:
            raise ExternalServiceError(f"Failed to process options chain for {ticker}", "yfinance", {"error": str(e)})
    
    def _process_option_row(self, row: pd.Series, option_type: str, expiry: str, ticker: str) -> Dict[str, Any]:
        """Process a single option row"""
        # Calculate Greeks
        greeks = None
        try:
            if row.get('impliedVolatility') and row.get('strike'):
                stock_price = row.get('lastPrice', 0)  # This would need current stock price
                if stock_price > 0:
                    greeks = self._calculate_greeks(
                        stock_price, row['strike'], expiry, 
                        row['impliedVolatility'], option_type.lower()
                    )
        except:
            pass
        
        return {
            "contract_symbol": f"{ticker.upper()}{expiry.replace('-', '')}{option_type[0]}{int(row['strike']*1000):08d}",
            "strike": row['strike'],
            "expiry": expiry,
            "option_type": option_type,
            "last_price": row.get('lastPrice'),
            "bid": row.get('bid'),
            "ask": row.get('ask'),
            "volume": row.get('volume'),
            "open_interest": row.get('openInterest'),
            "implied_volatility": row.get('impliedVolatility'),
            "greeks": greeks
        }
    
    def _calculate_greeks(self, stock_price: float, strike: float, expiry: str, 
                         iv: float, option_type: str = 'call') -> Dict[str, float]:
        """Calculate option Greeks using Black-Scholes model"""
        try:
            # Convert expiry to years
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
            time_to_expiry = (expiry_date - datetime.now()).days / 365.0
            
            if time_to_expiry <= 0 or iv <= 0 or stock_price <= 0 or strike <= 0:
                return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
            
            S = stock_price
            K = strike
            T = time_to_expiry
            r = 0.05  # Risk-free rate
            sigma = iv
            
            # Black-Scholes d1 and d2
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            # Standard normal PDF and CDF
            n_d1 = norm.cdf(d1)
            n_d2 = norm.cdf(d2)
            n_prime_d1 = norm.pdf(d1)
            
            # Greeks
            if option_type.lower() == 'call':
                delta = n_d1
                theta = (-(S * n_prime_d1 * sigma) / (2 * math.sqrt(T)) 
                         - r * K * math.exp(-r * T) * n_d2) / 365
            else:  # put
                delta = n_d1 - 1
                theta = (-(S * n_prime_d1 * sigma) / (2 * math.sqrt(T)) 
                         + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
            
            gamma = n_prime_d1 / (S * sigma * math.sqrt(T))
            vega = S * n_prime_d1 * math.sqrt(T) / 100  # Per 1% IV change
            
            return {
                'delta': round(delta, 3),
                'gamma': round(gamma, 4),
                'theta': round(theta, 3),
                'vega': round(vega, 3)
            }
        except Exception:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
    
    async def get_stock_history(self, ticker: str, period: str = "3mo", interval: str = "1d") -> Dict[str, Any]:
        """Get stock price history with technical indicators"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, self._get_stock_history_sync, ticker, period, interval
            )
            return result
        except Exception as e:
            raise ExternalServiceError(f"Failed to fetch history for {ticker}", "yfinance", {"error": str(e)})
    
    def _get_stock_history_sync(self, ticker: str, period: str, interval: str) -> Dict[str, Any]:
        """Synchronous stock history fetch"""
        stock = yf.Ticker(ticker)
        
        try:
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                return {"ticker": ticker.upper(), "error": "No historical data available"}
            
            # Convert to list of price points
            prices = []
            for date, row in hist.iterrows():
                prices.append({
                    "date": date.to_pydatetime(),
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close'],
                    "volume": int(row['Volume']),
                    "adj_close": row.get('Adj Close')
                })
            
            # Calculate technical indicators
            technicals = self._calculate_technicals(hist)
            
            return {
                "ticker": ticker.upper(),
                "period": period,
                "interval": interval,
                "prices": prices,
                "technicals": technicals
            }
            
        except Exception as e:
            raise ExternalServiceError(f"Failed to process history for {ticker}", "yfinance", {"error": str(e)})
    
    def _calculate_technicals(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            closes = hist['Close']
            
            # EMAs
            ema_20 = closes.ewm(span=20).iloc[-1]
            ema_50 = closes.ewm(span=50).iloc[-1]
            
            # RSI
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD
            exp1 = closes.ewm(span=12).mean()
            exp2 = closes.ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            
            # ATR
            high_low = hist['High'] - hist['Low']
            high_close = (hist['High'] - hist['Close'].shift()).abs()
            low_close = (hist['Low'] - hist['Close'].shift()).abs()
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            
            return {
                "ema_20": round(ema_20, 2) if not pd.isna(ema_20) else None,
                "ema_50": round(ema_50, 2) if not pd.isna(ema_50) else None,
                "rsi": round(rsi, 2) if not pd.isna(rsi) else None,
                "macd": {
                    "macd": round(macd.iloc[-1], 4) if not pd.isna(macd.iloc[-1]) else None,
                    "signal": round(signal.iloc[-1], 4) if not pd.isna(signal.iloc[-1]) else None,
                    "histogram": round((macd - signal).iloc[-1], 4) if not pd.isna((macd - signal).iloc[-1]) else None
                },
                "atr": round(atr, 2) if not pd.isna(atr) else None
            }
        except Exception:
            return {}
    
    async def close(self):
        """Close the thread pool executor"""
        self.executor.shutdown(wait=True)
