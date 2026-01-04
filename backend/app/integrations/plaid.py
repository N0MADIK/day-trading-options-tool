"""Plaid integration for banking and financial account access"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
from .base import BaseIntegration
from app.domain.errors import ExternalServiceError, ValidationError


class PlaidIntegration(BaseIntegration):
    """Integration with Plaid for banking and financial services"""
    
    def __init__(self):
        super().__init__()
        self.base_url = os.getenv('PLAID_BASE_URL', 'https://development.plaid.com')
        self.client_id = os.getenv('PLAID_CLIENT_ID')
        self.secret = os.getenv('PLAID_SECRET')
        
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate Plaid access token"""
        if not credentials.get('access_token'):
            raise ValidationError("Plaid access token is required")
        
        # Test the token by making a simple API call
        try:
            await self.get_accounts(credentials)
            return True
        except Exception:
            return False
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, str]:
        """Exchange Plaid Link public token for access token"""
        url = f"{self.base_url}/item/public_token/exchange"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'public_token': public_token
        }
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'access_token': response['access_token'],
            'item_id': response['item_id']
        }
    
    async def create_link_token(self, user_id: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a Plaid Link token for user authentication"""
        url = f"{self.base_url}/link/token/create"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'client_name': 'Day Trading Options Tool',
            'country_codes': ['US'],
            'language': 'en',
            'user': {
                'client_user_id': user_id
            },
            'products': ['accounts', 'transactions', 'investments', 'holdings'],
            'account_filters': {
                'investment': {
                    'account_subtypes': ['401k', 'brokerage', 'ira', 'roth']
                }
            }
        }
        
        if webhook_url:
            data['webhook'] = webhook_url
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'link_token': response['link_token'],
            'expiration': response['expiration'],
            'request_id': response['request_id']
        }
    
    async def test_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test connection to Plaid"""
        if not credentials.get('access_token'):
            raise ValidationError("Access token is required")
        
        url = f"{self.base_url}/item/get"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token']
        }
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'connected': True,
            'institution_id': response['item']['institution_id'],
            'item_id': response['item']['item_id'],
            'webhook': response['item']['webhook'],
            'available_products': response['item']['available_products'],
            'billed_products': response['item']['billed_products']
        }
    
    async def get_accounts(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get user accounts from Plaid"""
        url = f"{self.base_url}/accounts/get"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token']
        }
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'accounts': response['accounts'],
            'item': response['item'],
            'request_id': response['request_id']
        }
    
    async def get_transactions(
        self,
        credentials: Dict[str, str],
        start_date: datetime,
        end_date: datetime,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get transactions from Plaid"""
        url = f"{self.base_url}/transactions/get"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        if account_ids:
            data['account_ids'] = account_ids
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'accounts': response['accounts'],
            'transactions': response['transactions'],
            'total_transactions': response['total_transactions'],
            'request_id': response['request_id']
        }
    
    async def get_holdings(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get investment holdings from Plaid"""
        url = f"{self.base_url}/investments/holdings/get"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token']
        }
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'accounts': response['accounts'],
            'holdings': response['holdings'],
            'securities': response['securities'],
            'request_id': response['request_id']
        }
    
    async def get_investment_transactions(
        self,
        credentials: Dict[str, str],
        start_date: datetime,
        end_date: datetime,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get investment transactions from Plaid"""
        url = f"{self.base_url}/investments/transactions/get"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        if account_ids:
            data['account_ids'] = account_ids
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'accounts': response['accounts'],
            'investment_transactions': response['investment_transactions'],
            'securities': response['securities'],
            'total_investment_transactions': response['total_investment_transactions'],
            'request_id': response['request_id']
        }
    
    async def refresh_transactions(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Refresh transactions data"""
        url = f"{self.base_url}/transactions/refresh"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token']
        }
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'request_id': response['request_id']
        }
    
    async def remove_item(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Remove Plaid item (disconnect account)"""
        url = f"{self.base_url}/item/remove"
        
        data = {
            'client_id': self.client_id,
            'secret': self.secret,
            'access_token': credentials['access_token']
        }
        
        response = await self._make_request(
            'POST',
            url,
            json_data=data
        )
        
        return {
            'request_id': response['request_id']
        }
