"""
SnapTrade Connector

Integration with SnapTrade API for aggregating brokerage accounts.
Replaces the generic AggregatorConnector.
"""
import os
import json
import requests
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .models import (
    SourceType, SyncMode, AccountType, AccountSubtype, 
    SecurityType, TransactionType
)
from .connectors import (
    BaseConnector, LinkSessionResult, ExchangeResult, SyncResult,
    HealthCheckResult, AccountDTO, HoldingDTO, TransactionDTO
)
import sys


class SnapTradeConnector(BaseConnector):
    """
    Connector for SnapTrade API.
    
    Manages user registration, connection linking, and data syncing.
    """
    
    source_type = SourceType.SNAPTRADE
    BASE_URL = "https://api.snaptrade.com/api/v1"
    
    def __init__(self):
        self.client_id = os.environ.get("SNAPTRADE_CLIENT_ID", "")
        print(os.environ.get("SNAPTRADE_CLIENT_ID", ""), file=sys.stdout)
        self.consumer_key = os.environ.get("SNAPTRADE_CONSUMER_KEY", "")
        self._demo_mode = os.environ.get("FINANCE_DEMO_MODE", "true").lower() == "true"
        
    def _is_demo_mode(self) -> bool:
        """Check if running in demo mode (no real API calls)."""
        return self._demo_mode or not self.client_id or not self.consumer_key

    def _signed_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, json_data: Dict[str, Any] = None) -> requests.Response:
        """
        Execute a signed request to SnapTrade API.
        Handles timestamp and HMAC-SHA256 signature generation.
        """
        if params is None:
            params = {}
        # Allow json_data to be None for requests with no body
            
        # Add timestamp and clientId to params
        params["clientId"] = self.client_id
        params["timestamp"] = str(int(time.time()))
        
        # Sort params for consistency (SnapTrade requires sorted query params)
        # Construct query string
        query_string = urllib.parse.urlencode(sorted(params.items()))
        
        # Prepare content for signature
        # Note: endpoint should be the full path e.g. /api/v1/snapTrade/registerUser
        path = f"/api/v1{endpoint}"
        
        sig_object = {
            "content": json_data,
            "path": path,
            "query": query_string
        }
        
        # Serialize with no spaces
        sig_data = json.dumps(sig_object, separators=(',', ':'), sort_keys=True)
        
        # Generate Signature
        signature = hmac.new(
            self.consumer_key.encode('utf-8'),
            sig_data.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        headers = {
            "Content-Type": "application/json",
            "Signature": signature_b64
        }
        
        # FIX: Append query string to URL manually to ensure what we signed is EXACTLY what is sent.
        # Passing params=params to requests() might result in different order/encoding.
        url = f"{self.BASE_URL}{endpoint}?{query_string}"
        
        print(f"DEBUG: Request {method} {url}", file=sys.stdout)
        # print(f"DEBUG: Sig Data: {sig_data}", file=sys.stdout)
        
        return requests.request(method, url, json=json_data, headers=headers)


    def create_link_session(self, user_id: str, user_secret: str = None, **kwargs) -> LinkSessionResult:
        """
        Register user (if needed) and generate Connection Portal URL.
        """
        if self._is_demo_mode():
            # Mock flow
            mock_secret = f"mock-secret-{user_id}"
            return LinkSessionResult(
                success=True,
                link_url="https://app.snaptrade.com/demo-mock", # Placeholder
                link_token=mock_secret,
                expires_at=(datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z",
                session_id=f"session_{user_id}"
            )

        try:
            if not self.client_id or not self.consumer_key:
                return LinkSessionResult(success=False, error="Missing SnapTrade API credentials")

            # 1. Register User (idempotent) or Use Secret
            if not user_secret:
                # Use _signed_request which handles timestamp/signature/clientId
                resp = self._signed_request("POST", "/snapTrade/registerUser", json_data={"userId": user_id})
                
                print(f"DEBUG: Register response: {resp.status_code} {resp.text}", file=sys.stdout)
                
                if resp.status_code == 400 and "1010" in resp.text: # User already exists
                    # If we don't have the secret, and user exists, we are stuck. 
                    # For "default" user (dev), we delete and re-create.
                    print(f"DEBUG: User {user_id} exists but missing secret. Deleting...", file=sys.stdout)
                    del_resp = self._signed_request("POST", "/snapTrade/deleteUser", json_data={"userId": user_id})
                    print(f"DEBUG: Delete response: {del_resp.status_code}", file=sys.stdout)
                    
                    if del_resp.status_code == 200:
                        print("DEBUG: Retrying registration...", file=sys.stdout)
                        time.sleep(1) # Wait for propagation maybe?
                        resp = self._signed_request("POST", "/snapTrade/registerUser", json_data={"userId": user_id})
                        print(f"DEBUG: Retry Register response: {resp.status_code}", file=sys.stdout)
                
                if resp.status_code not in [200, 201]:
                    return LinkSessionResult(success=False, error=f"Registration failed: {resp.status_code} {resp.text}")

                user_secret = resp.json().get("userSecret")
                print(f"DEBUG: Got userSecret: {user_secret[:5] if user_secret else 'None'}...", file=sys.stdout)
            
            if not user_secret:
                 return LinkSessionResult(success=False, error="Registration succeeded but no userSecret returned")

            # 2. Login User
            # login params: userId, userSecret. clientId/timestamp added by _signed_request
            login_params = {
                "userId": user_id,
                "userSecret": user_secret
            }
            
            login_resp = self._signed_request("POST", "/snapTrade/login", params=login_params)
            print(f"DEBUG: Login response: {login_resp.status_code} {login_resp.text}", file=sys.stdout)
            
            if login_resp.status_code != 200:
                return LinkSessionResult(success=False, error=f"Login failed: {login_resp.status_code} {login_resp.text}")
                
            redirect_uri = login_resp.json().get("redirectURI")
            
            return LinkSessionResult(
                success=True,
                link_url=redirect_uri,
                link_token=user_secret, # Pass secret back to be stored/used in exchange
                expires_at=None 
            )
            
        except Exception as e:
            return LinkSessionResult(success=False, error=f"SnapTrade Connection Error: {str(e)}")

    def exchange_link_artifact(self, user_id: str, artifact: Dict[str, Any]) -> ExchangeResult:
        """
        For SnapTrade, 'exchange' just confirms we have the user secret.
        The artifact should contain 'userSecret' (passed from create_link_session to frontend and back).
        """
        user_secret = artifact.get("userSecret") or artifact.get("link_token")
        
        if not user_secret:
             return ExchangeResult(success=False, error="Missing userSecret")
             
        # In a real scenario, we might want to list accounts here to verify connectivity
        # But simply storing the credential is enough.
        
        return ExchangeResult(
            success=True,
            auth_data={
                "user_id": user_id,
                "user_secret": user_secret,
                "client_id": self.client_id # Store config too? Not strictly necessary but context is good
            }
        )

    def sync_connection(
        self, 
        connection_id: int, 
        auth_data: Dict[str, Any],
        mode: SyncMode = SyncMode.INCREMENTAL,
        last_synced_at: Optional[str] = None
    ) -> SyncResult:
        
        if self._is_demo_mode():
            return self._sync_mock_data()

        user_id = auth_data.get("user_id")
        user_secret = auth_data.get("user_secret")
        
        if not user_id or not user_secret:
            return SyncResult(success=False, errors=["Missing auth credentials"])
            
        try:
            # 1. Fetch Accounts
            # _signed_request adds clientId/timestamp. We add userId/userSecret
            params = {"userId": user_id, "userSecret": user_secret}
            
            acct_resp = self._signed_request("GET", "/accounts", params=params)
            
            if acct_resp.status_code != 200:
                 return SyncResult(success=False, errors=[f"Failed to fetch accounts: {acct_resp.text}"])
                 
            st_accounts = acct_resp.json()
            
            accounts = []
            holdings_map = {}
            transactions_map = {}
            
            for acc in st_accounts:
                st_id = acc.get("id")
                
                # Map Account
                account_dto = AccountDTO(
                    external_id=st_id,
                    name=acc.get("name", "Unknown Account"),
                    account_type=AccountType.BROKERAGE, # Default, maybe infer from properties?
                    currency=acc.get("currency", {}).get("code", "USD"),
                    masked_number=acc.get("number")
                )
                accounts.append(account_dto)
                
                # 2. Fetch Holdings for Account
                hold_resp = self._signed_request("GET", f"/accounts/{st_id}/holdings", params=params)
                
                acc_holdings = []
                if hold_resp.status_code == 200:
                    st_holdings = hold_resp.json().get("positions", []) if isinstance(hold_resp.json(), dict) else hold_resp.json()
                    # SnapTrade response structure varies, assuming list of positions
                    # Depending on endpoint, it might be { account: ..., positions: [...] }
                    
                    # Note: /accounts/{id}/holdings might return the list directly or wrapped.
                    # Adjusted based on typical SnapTrade response: { accountId: ..., positions: [...] } or list.
                    # Let's assume list of AccountHoldings? No, endpoint is specific to account.
                    
                    # Safer to check type
                    positions = st_holdings.get("positions", []) if isinstance(st_holdings, dict) else st_holdings
                    
                    for pos in positions:
                        symbol = pos.get("symbol", {}).get("symbol")
                        if not symbol: continue
                        
                        acc_holdings.append(HoldingDTO(
                            symbol=symbol,
                            security_name=pos.get("symbol", {}).get("description", symbol),
                            security_type=SecurityType.UNKNOWN,
                            quantity=float(pos.get("units", 0) or 0),
                            price=float(pos.get("price", 0) or 0),
                            value=float(pos.get("total_value", 0) or 0),
                            cost_basis_total=float(pos.get("average_purchase_price", 0) or 0) * float(pos.get("units", 0) or 0)
                        ))
                
                holdings_map[st_id] = acc_holdings
                
                # 3. Fetch Transactions (optional, keep light for now)
                # ...
                
            return SyncResult(
                success=True,
                accounts=accounts,
                holdings=holdings_map,
                transactions=transactions_map
            )

        except Exception as e:
            return SyncResult(success=False, errors=[str(e)])

    def _sync_mock_data(self) -> SyncResult:
        # Return same mock structure as Aggregator but tailored if needed
        # Reusing the Aggregator mock logic for simplicity
        accounts = [
            AccountDTO("acc_st_1", "SnapTrade Brokerage", AccountType.BROKERAGE, AccountSubtype.TAXABLE, "USD", "****1111"),
            AccountDTO("acc_st_2", "SnapTrade IRA", AccountType.RETIREMENT, AccountSubtype.ROTH_IRA, "USD", "****2222")
        ]
        
        holdings = {
            "acc_st_1": [
                HoldingDTO("NVDA", "NVIDIA Corp", SecurityType.EQUITY, 10.0, 480.00, 4800.00, 4000.00, 400.00),
                HoldingDTO("AMD", "Advanced Micro Devices", SecurityType.EQUITY, 50.0, 140.00, 7000.00, 6000.00, 120.00)
            ],
            "acc_st_2": [
                HoldingDTO("SPY", "SPDR S&P 500 ETF Trust", SecurityType.ETF, 20.0, 470.00, 9400.00, 8000.00, 400.00)
            ]
        }
        
        return SyncResult(True, accounts, holdings, {})

    def health_check(self, auth_data: Dict[str, Any]) -> HealthCheckResult:
        if self._is_demo_mode():
             return HealthCheckResult(True, False, "Demo Mode Healthy")
             
        # Maybe call /users endpoint to verify credentials?
        return HealthCheckResult(True, False, "Healthy")

