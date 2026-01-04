"""Alpaca integration for stock and crypto trading"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
from .base import BaseIntegration
from app.domain.errors import ExternalServiceError, ValidationError


class AlpacaIntegration(BaseIntegration):
    """Integration with Alpaca for stock and crypto trading"""
    
    def __init__(self):
        super().__init__()
        self.live_base_url = 'https://api.alpaca.markets'
        self.paper_base_url = 'https://paper-api.alpaca.markets'
        self.data_base_url = 'https://data.alpaca.markets'
        
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate Alpaca API credentials"""
        required_fields = ['api_key', 'secret_key']
        for field in required_fields:
            if not credentials.get(field):
                raise ValidationError(f"Alpaca {field} is required")
        
        # Test the credentials by making a simple API call
        try:
            await self.test_connection(credentials)
            return True
        except Exception:
            return False
    
    def _get_base_url(self, is_paper: bool = True) -> str:
        """Get the appropriate base URL based on paper/live mode"""
        return self.paper_base_url if is_paper else self.live_base_url
    
    async def test_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test connection to Alpaca"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/account"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'connected': True,
            'account_number': response['account_number'],
            'status': response['status'],
            'crypto_status': response['crypto_status'],
            'currency': response['currency'],
            'buying_power': response['buying_power'],
            'portfolio_value': response['portfolio_value'],
            'pattern_day_trader': response['pattern_day_trader'],
            'trading_blocked': response['trading_blocked'],
            'transfers_blocked': response['transfers_blocked'],
            'account_blocked': response['account_blocked'],
            'created_at': response['created_at']
        }
    
    async def get_accounts(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get account information from Alpaca"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/account"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'account': response,
            'is_paper_trading': is_paper
        }
    
    async def get_positions(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get all open positions"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/positions"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'positions': response
        }
    
    async def get_orders(
        self,
        credentials: Dict[str, str],
        status: Optional[str] = None,
        limit: int = 100,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get orders from Alpaca"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/orders"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        params = {'limit': limit}
        if status:
            params['status'] = status
        if after:
            params['after'] = after.isoformat()
        if until:
            params['until'] = until.isoformat()
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'orders': response
        }
    
    async def place_order(
        self,
        credentials: Dict[str, str],
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Place a new order"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/orders"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        # Basic order validation
        required_fields = ['symbol', 'qty', 'side', 'type', 'time_in_force']
        for field in required_fields:
            if field not in order_data:
                raise ValidationError(f"Order field '{field}' is required")
        
        response = await self._make_request(
            'POST',
            url,
            headers=headers,
            json_data=order_data
        )
        
        return response
    
    async def cancel_order(self, credentials: Dict[str, str], order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/orders/{order_id}"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        response = await self._make_request(
            'DELETE',
            url,
            headers=headers
        )
        
        return {
            'order_cancelled': True,
            'order_id': order_id
        }
    
    async def get_portfolio_history(
        self,
        credentials: Dict[str, str],
        period: str = "1M",
        timeframe: str = "1D"
    ) -> Dict[str, Any]:
        """Get portfolio history"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/account/portfolio/history"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        params = {
            'period': period,
            'timeframe': timeframe
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return response
    
    async def get_market_data(
        self,
        credentials: Dict[str, str],
        symbols: List[str],
        timeframe: str = "1Day",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Get market data for symbols"""
        url = f"{self.data_base_url}/v2/stocks/bars"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        params = {
            'symbols': ','.join(symbols),
            'timeframe': timeframe,
            'limit': limit
        }
        
        if start:
            params['start'] = start.isoformat()
        if end:
            params['end'] = end.isoformat()
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'bars': response.get('bars', {}),
            'next_page_token': response.get('next_page_token')
        }
    
    async def get_latest_quotes(
        self,
        credentials: Dict[str, str],
        symbols: List[str]
    ) -> Dict[str, Any]:
        """Get latest quotes for symbols"""
        url = f"{self.data_base_url}/v2/stocks/quotes/latest"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        params = {
            'symbols': ','.join(symbols)
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'quotes': response.get('quotes', {})
        }
    
    async def get_watchlists(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get all watchlists"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/watchlists"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'watchlists': response
        }
    
    async def create_watchlist(
        self,
        credentials: Dict[str, str],
        name: str,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """Create a new watchlist"""
        is_paper = credentials.get('is_paper_trading', True)
        url = f"{self._get_base_url(is_paper)}/v2/watchlists"
        
        headers = {
            'APCA-API-KEY-ID': credentials['api_key'],
            'APCA-API-SECRET-KEY': credentials['secret_key']
        }
        
        data = {
            'name': name,
            'symbols': symbols
        }
        
        response = await self._make_request(
            'POST',
            url,
            headers=headers,
            json_data=data
        )
        
        return response
