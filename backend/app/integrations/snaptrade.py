"""SnapTrade integration for connecting brokerage accounts"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import asyncio
from functools import partial

# SDK Imports
from snaptrade_client import SnapTrade, ApiException

from .base import BaseIntegration
from app.domain.errors import ExternalServiceError, ValidationError

from app.core.config import settings

class SnapTradeIntegration(BaseIntegration):
    """Integration with SnapTrade using the Official SDK"""
    
    def __init__(self):
        super().__init__()
        
        if not settings.snaptrade_client_id or not settings.snaptrade_consumer_key:
            raise ValueError("SnapTrade credentials not configured in settings")
            
        # Initialize the official client
        self.client = SnapTrade(
            consumer_key=settings.snaptrade_consumer_key,
            client_id=settings.snaptrade_client_id
        )
        
        # Mapping of common frontend slugs to SnapTrade broker slugs
        self.broker_slug_map = {
            'robinhood': 'ROBINHOOD',
            'vanguard': 'VANGUARD',
            'fidelity': 'FIDELITY',
            'td-ameritrade': 'TD',
            'tdameritrade': 'TD',
            'schwab': 'SCHWAB',
            'etrade': 'ETRADE',
            'e*trade': 'ETRADE',
            'interactive-brokers': 'INTERACTIVE',
            'alpaca': 'ALPACA',
            'webull': 'WEBULL',
            'tastytrade': 'TASTYTRADE',
        }
    
    async def _run_sdk(self, func, *args, **kwargs):
        """
        Helper to run synchronous SDK calls in a thread pool 
        to avoid blocking the async event loop.
        """
        loop = asyncio.get_running_loop()
        # partial allows us to pass kwargs to run_in_executor
        func_part = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_part)

    def _normalize_broker_slug(self, slug: str) -> str:
        """Normalize broker slug to SnapTrade's expected format."""
        normalized = self.broker_slug_map.get(slug.lower())
        if normalized:
            return normalized
        return slug.upper().replace('-', '_')

    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate SnapTrade user credentials via a lightweight API call"""
        if not credentials.get('user_secret') or not credentials.get('user_id'):
            return False
            
        try:
            # Attempt to list accounts to verify creds
            await self._run_sdk(
                self.client.account_information.list_user_accounts,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret']
                }
            )
            return True
        except ApiException:
            return False
        except Exception:
            return False

    async def test_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Test connection to SnapTrade (Required by BaseIntegration).
        Validates the user_secret/user_id pair by attempting to list accounts.
        """
        if not credentials.get('user_secret') or not credentials.get('user_id'):
             return {
                'connected': False, 
                'error': 'Missing user_id or user_secret'
            }
            
        try:
            # We use list_user_accounts as a proxy for "is this connection valid?"
            # If creds are wrong, this raises ApiException (401/403)
            await self._run_sdk(
                self.client.account_information.list_user_accounts,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret']
                }
            )
            return {
                'connected': True, 
                'details': 'Credentials validated successfully'
            }
        except ApiException as e:
            return {
                'connected': False, 
                'error': f"SnapTrade Error: {e.status} - {e.body}"
            }
        except Exception as e:
            return {
                'connected': False, 
                'error': str(e)
            }

    async def register_user(self, user_id: str) -> Dict[str, Any]:
        """Register a new SnapTrade user"""
        print(f"DEBUG: Registering SnapTrade user: {user_id}")
        try:
            print(f"DEBUG: Calling SDK register_snap_trade_user...")
            response = await self._run_sdk(
                self.client.authentication.register_snap_trade_user,
                body={"userId": user_id}
            )
            print(f"DEBUG: Registration successful, got secret: {response.body['userSecret'][:5]}...")
            
            return {
                'user_secret': response.body['userSecret'],
                'user_id': user_id
            }
        except ApiException as e:
            print(f"DEBUG: SnapTrade SDK Error: {e.status} - {e.body}")
            raise ExternalServiceError(f"SnapTrade Registration Failed: {e.body}")

    async def initiate_connection(
        self,
        credentials: Dict[str, str],
        brokerage_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Generates a connection link"""
        user_id = credentials.get('user_id')
        user_secret = credentials.get('user_secret')
        
        if not user_id or not user_secret:
            raise ValidationError("Both user_id and user_secret are required")

        normalized_broker = self._normalize_broker_slug(brokerage_id)

        try:
            response = await self._run_sdk(
                self.client.authentication.login_snap_trade_user,
                query_params={
                    "userId": user_id,
                    "userSecret": user_secret,
                },
                body={
                    "broker": normalized_broker,
                    "immediateRedirect": True,
                    "customRedirect": redirect_uri
                }
            )
            
            return {
                'redirect_uri': response.body.get('redirectURI'),
                'authorization_url': response.body.get('redirectURI')
            }
        except ApiException as e:
            raise ExternalServiceError(f"Failed to generate login link: {e.body}")

    async def get_accounts(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get brokerage accounts"""
        try:
            response = await self._run_sdk(
                self.client.account_information.list_user_accounts,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret']
                }
            )
            return {'accounts': response.body}
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch accounts: {e.body}")

    async def get_account_details(self, credentials: Dict[str, str], account_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific account"""
        try:
            response = await self._run_sdk(
                self.client.account_information.get_user_account_details,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret'],
                    "accountId": account_id
                }
            )
            return response.body
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch account details: {e.body}")

    async def get_holdings(self, credentials: Dict[str, str], account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get holdings/positions"""
        try:
            if account_id:
                # Fetch positions for specific account
                response = await self._run_sdk(
                    self.client.account_information.get_user_account_positions,
                    query_params={
                        "userId": credentials['user_id'],
                        "userSecret": credentials['user_secret'],
                        "accountId": account_id
                    }
                )
                return {
                    'holdings': response.body,
                    # Note: Total value often requires a separate call to balances if not in positions response
                    'total_value': 0 
                }
            else:
                # Fetch all holdings
                response = await self._run_sdk(
                    self.client.account_information.get_all_user_holdings,
                    query_params={
                        "userId": credentials['user_id'],
                        "userSecret": credentials['user_secret']
                    }
                )
                return {
                    'holdings': response.body,
                    'total_value': response.body.get('total_value')
                }
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch holdings: {e.body}")

    async def get_transactions(
        self,
        credentials: Dict[str, str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transactions (activities)"""
        try:
            query_params = {
                "userId": credentials['user_id'],
                "userSecret": credentials['user_secret']
            }
            if start_date:
                query_params["startDate"] = start_date.strftime('%Y-%m-%d')
            if end_date:
                query_params["endDate"] = end_date.strftime('%Y-%m-%d')
            if account_id:
                query_params["accounts"] = account_id 

            response = await self._run_sdk(
                self.client.transactions_and_reporting.get_activities,
                query_params=query_params
            )
            
            return {'activities': response.body}
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch transactions: {e.body}")

    async def get_performance(
        self,
        credentials: Dict[str, str],
        account_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            query_params = {
                "userId": credentials['user_id'],
                "userSecret": credentials['user_secret']
            }
            if start_date:
                query_params["startDate"] = start_date.strftime('%Y-%m-%d')
            if end_date:
                query_params["endDate"] = end_date.strftime('%Y-%m-%d')
            if account_id:
                query_params["accounts"] = account_id

            response = await self._run_sdk(
                self.client.transactions_and_reporting.get_reporting_custom_range,
                query_params=query_params
            )
            return response.body
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch performance: {e.body}")

    async def get_balances(self, credentials: Dict[str, str], account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get account balances"""
        try:
            if account_id:
                response = await self._run_sdk(
                    self.client.account_information.get_user_account_balance,
                    query_params={
                        "userId": credentials['user_id'],
                        "userSecret": credentials['user_secret'],
                        "accountId": account_id
                    }
                )
                return {'balances': response.body}
            else:
                # Fallback to fetching all accounts if no ID specified, or iterate logic as needed
                # SnapTrade API typically requires accountId for balance specific endpoint
                raise ValidationError("account_id is required for fetching balances")
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch balances: {e.body}")

    async def get_brokerages(self) -> Dict[str, Any]:
        """Get list of supported brokerages"""
        try:
            response = await self._run_sdk(
                self.client.reference_data.list_all_brokerages
            )
            return {'brokerages': response.body}
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch brokerages: {e.body}")

    async def get_connection_status(
        self,
        credentials: Dict[str, str],
        brokerage_authorization_id: str
    ) -> Dict[str, Any]:
        """Check the status of a brokerage connection"""
        try:
            response = await self._run_sdk(
                self.client.connections.detail_brokerage_authorization,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret'],
                    "authorizationId": brokerage_authorization_id
                }
            )
            
            data = response.body
            return {
                'status': 'connected' if not data.get('disabled') else 'broken', # simplified mapping
                'brokerage': data.get('brokerage'),
                'created_date': data.get('created_date'),
                'updated_date': data.get('updated_date'),
                'raw_status': data # Return full object for detailed inspection
            }
        except ApiException as e:
            raise ExternalServiceError(f"Failed to fetch connection status: {e.body}")

    async def delete_connection(
        self,
        credentials: Dict[str, str],
        brokerage_authorization_id: str
    ) -> Dict[str, Any]:
        """Delete a brokerage connection"""
        try:
            await self._run_sdk(
                self.client.connections.remove_brokerage_authorization,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret'],
                    "authorizationId": brokerage_authorization_id
                }
            )
            
            return {
                'deleted': True,
                'brokerage_authorization_id': brokerage_authorization_id
            }
        except ApiException as e:
            raise ExternalServiceError(f"Failed to delete connection: {e.body}")

    async def refresh_holdings(self, credentials: Dict[str, str], account_id: str) -> Dict[str, Any]:
        """
        Refresh holdings data.
        Note: SnapTrade refreshes by Connection (Authorization), not Account.
        We must find the authorization ID for this account first.
        """
        try:
            # 1. Get Account Details to find the Authorization ID
            account_response = await self._run_sdk(
                self.client.account_information.get_user_account_details,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret'],
                    "accountId": account_id
                }
            )
            
            auth_id = account_response.body.get('brokerage_authorization')
            if not auth_id:
                raise ValidationError("Could not find authorization ID for this account")

            # 2. Trigger Refresh on the Authorization
            await self._run_sdk(
                self.client.connections.refresh_brokerage_authorization,
                query_params={
                    "userId": credentials['user_id'],
                    "userSecret": credentials['user_secret'],
                    "authorizationId": auth_id
                }
            )
            
            return {
                'refresh_initiated': True,
                'account_id': account_id
            }
        except ApiException as e:
            raise ExternalServiceError(f"Failed to refresh holdings: {e.body}")