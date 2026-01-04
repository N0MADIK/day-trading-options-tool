"""SnapTrade integration for connecting brokerage accounts"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
import hashlib
import hmac
import time
from .base import BaseIntegration
from app.domain.errors import ExternalServiceError, ValidationError


class SnapTradeIntegration(BaseIntegration):
    """Integration with SnapTrade for brokerage account connections"""
    
    def __init__(self):
        super().__init__()
        self.base_url = 'https://api.snaptrade.com/api/v1'
        self.client_id = os.getenv('SNAPTRADE_CLIENT_ID')
        self.consumer_key = os.getenv('SNAPTRADE_CONSUMER_KEY')
        
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate SnapTrade user credentials"""
        if not credentials.get('user_secret'):
            raise ValidationError("SnapTrade user secret is required")
        
        # Test the credentials by making a simple API call
        try:
            await self.test_connection(credentials)
            return True
        except Exception:
            return False
    
    def _generate_signature(self, user_secret: str, timestamp: str, path: str) -> str:
        """Generate HMAC signature for SnapTrade API requests"""
        message = f"{self.consumer_key}{timestamp}{path}"
        signature = hmac.new(
            user_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return signature.hex()
    
    def _build_auth_headers(self, user_secret: str, path: str) -> Dict[str, str]:
        """Build authentication headers for SnapTrade"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(user_secret, timestamp, path)
        
        return {
            'clientId': self.client_id,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json'
        }
    
    async def register_user(self, user_id: str) -> Dict[str, Any]:
        """Register a new SnapTrade user"""
        path = '/snapTrade/registerUser'
        url = f"{self.base_url}{path}"
        
        headers = {
            'clientId': self.client_id,
            'Content-Type': 'application/json'
        }
        
        data = {
            'userId': user_id
        }
        
        response = await self._make_request(
            'POST',
            url,
            headers=headers,
            json_data=data
        )
        
        return {
            'user_secret': response['userSecret'],
            'user_id': user_id
        }
    
    async def test_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test connection to SnapTrade"""
        path = '/holdings'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        try:
            response = await self._make_request(
                'GET',
                url,
                headers=headers
            )
            
            return {
                'connected': True,
                'total_holdings': len(response.get('holdings', []))
            }
        except UnauthorizedError:
            return {
                'connected': False,
                'error': 'Invalid credentials'
            }
    
    async def get_accounts(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get brokerage accounts from SnapTrade"""
        path = '/accounts'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'accounts': response
        }
    
    async def get_account_details(self, credentials: Dict[str, str], account_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific account"""
        path = f'/accounts/{account_id}'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return response
    
    async def get_holdings(self, credentials: Dict[str, str], account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get holdings/positions from SnapTrade"""
        path = '/holdings'
        url = f"{self.base_url}{path}"
        
        if account_id:
            url += f"?accountId={account_id}"
            
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'holdings': response.get('holdings', []),
            'total_value': response.get('totalValue', 0)
        }
    
    async def get_transactions(
        self,
        credentials: Dict[str, str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transactions from SnapTrade"""
        path = '/activities'
        url = f"{self.base_url}{path}"
        
        params = []
        if start_date:
            params.append(f"startDate={start_date.strftime('%Y-%m-%d')}")
        if end_date:
            params.append(f"endDate={end_date.strftime('%Y-%m-%d')}")
        if account_id:
            params.append(f"accountId={account_id}")
            
        if params:
            url += f"?{'&'.join(params)}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'activities': response.get('activities', [])
        }
    
    async def get_performance(
        self,
        credentials: Dict[str, str],
        account_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance metrics"""
        path = '/performance'
        url = f"{self.base_url}{path}"
        
        params = []
        if account_id:
            params.append(f"accountId={account_id}")
        if start_date:
            params.append(f"startDate={start_date.strftime('%Y-%m-%d')}")
        if end_date:
            params.append(f"endDate={end_date.strftime('%Y-%m-%d')}")
            
        if params:
            url += f"?{'&'.join(params)}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return response
    
    async def get_balances(self, credentials: Dict[str, str], account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get account balances"""
        path = '/accounts/balances'
        url = f"{self.base_url}{path}"
        
        if account_id:
            url += f"?accountId={account_id}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'balances': response
        }
    
    async def get_brokerages(self) -> Dict[str, Any]:
        """Get list of supported brokerages"""
        path = '/brokerages'
        url = f"{self.base_url}{path}"
        
        headers = {
            'clientId': self.client_id,
            'Content-Type': 'application/json'
        }
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'brokerages': response
        }
    
    async def initiate_connection(
        self,
        credentials: Dict[str, str],
        brokerage_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Initiate OAuth connection to a brokerage"""
        path = f'/brokerages/{brokerage_id}/authorize'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        data = {
            'redirectUri': redirect_uri,
            'clientId': self.client_id
        }
        
        response = await self._make_request(
            'POST',
            url,
            headers=headers,
            json_data=data
        )
        
        return {
            'authorization_url': response['authorizationUrl'],
            'brokerage_authorization_id': response['brokerageAuthorizationId']
        }
    
    async def get_connection_status(
        self,
        credentials: Dict[str, str],
        brokerage_authorization_id: str
    ) -> Dict[str, Any]:
        """Check the status of a brokerage connection"""
        path = f'/brokerageAuthorizations/{brokerage_authorization_id}'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'GET',
            url,
            headers=headers
        )
        
        return {
            'status': response.get('status'),
            'brokerage': response.get('brokerage'),
            'created_date': response.get('createdDate'),
            'updated_date': response.get('updatedDate')
        }
    
    async def delete_connection(
        self,
        credentials: Dict[str, str],
        brokerage_authorization_id: str
    ) -> Dict[str, Any]:
        """Delete a brokerage connection"""
        path = f'/brokerageAuthorizations/{brokerage_authorization_id}'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        await self._make_request(
            'DELETE',
            url,
            headers=headers
        )
        
        return {
            'deleted': True,
            'brokerage_authorization_id': brokerage_authorization_id
        }
    
    async def refresh_holdings(self, credentials: Dict[str, str], account_id: str) -> Dict[str, Any]:
        """Refresh holdings data for an account"""
        path = f'/accounts/{account_id}/refresh'
        url = f"{self.base_url}{path}"
        
        headers = self._build_auth_headers(credentials['user_secret'], path)
        
        response = await self._make_request(
            'POST',
            url,
            headers=headers
        )
        
        return {
            'refresh_initiated': True,
            'account_id': account_id
        }
