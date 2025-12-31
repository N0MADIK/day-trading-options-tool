"""
Aggregator Connector (Plaid-style)

Placeholder implementation for Plaid or similar aggregator APIs.
Replace with actual Plaid SDK calls when ready to integrate.
"""
import os
import json
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


class AggregatorConnector(BaseConnector):
    """
    Connector for aggregator APIs (Plaid, Finicity, Yodlee, MX, Akoya).
    
    When FINANCE_DEMO_MODE=true, returns mock data for development.
    When false, integrates with actual Plaid SDK.
    """
    
    source_type = SourceType.AGGREGATOR
    
    def __init__(self):
        self.client_id = os.environ.get("PLAID_CLIENT_ID", "")
        self.secret = os.environ.get("PLAID_SECRET", "")
        self.environment = os.environ.get("PLAID_ENV", "sandbox")
        self._demo_mode = os.environ.get("FINANCE_DEMO_MODE", "true").lower() == "true"
    
    def _is_demo_mode(self) -> bool:
        """Check if running in demo mode (no real API calls)."""
        return self._demo_mode or not self.client_id or not self.secret
    
    def create_link_session(self, user_id: str, **kwargs) -> LinkSessionResult:
        """
        Create a Plaid Link token for the user.
        
        In production, this would call:
            plaid.link_token_create(...)
        """
        # Placeholder - would create actual Plaid link token
        mock_link_token = f"link-sandbox-{user_id}-{datetime.utcnow().timestamp()}"
        
        return LinkSessionResult(
            success=True,
            link_token=mock_link_token,
            expires_at=(datetime.utcnow() + timedelta(hours=4)).isoformat() + "Z",
            session_id=f"session_{user_id}"
        )
    
    def exchange_link_artifact(self, user_id: str, artifact: Dict[str, Any]) -> ExchangeResult:
        """
        Exchange public_token for access_token.
        
        In production, this would call:
            plaid.item_public_token_exchange(public_token)
        """
        public_token = artifact.get("public_token")
        
        if not public_token:
            return ExchangeResult(success=False, error="Missing public_token")
        
        # Placeholder - would exchange for real access token
        mock_access_token = f"access-sandbox-{user_id}-{datetime.utcnow().timestamp()}"
        mock_item_id = f"item_{user_id}"
        
        return ExchangeResult(
            success=True,
            auth_data={
                "access_token": mock_access_token,
                "item_id": mock_item_id,
                "institution_id": artifact.get("institution_id", "ins_placeholder")
            }
        )
    
    def sync_connection(
        self, 
        connection_id: int, 
        auth_data: Dict[str, Any],
        mode: SyncMode = SyncMode.INCREMENTAL,
        last_synced_at: Optional[str] = None
    ) -> SyncResult:
        """
        Sync investment data from the aggregator.
        
        In production, this would call:
            - plaid.investments_holdings_get()
            - plaid.investments_transactions_get()
        """
        access_token = auth_data.get("access_token")
        
        if not access_token:
            return SyncResult(success=False, errors=["Missing access_token"])
        
        # Mock data for development
        accounts = [
            AccountDTO(
                external_id="acc_brokerage_1",
                name="Individual Brokerage",
                account_type=AccountType.BROKERAGE,
                account_subtype=AccountSubtype.TAXABLE,
                currency="USD",
                masked_number="****4567"
            ),
            AccountDTO(
                external_id="acc_retirement_1",
                name="Roth IRA",
                account_type=AccountType.RETIREMENT,
                account_subtype=AccountSubtype.ROTH_IRA,
                currency="USD",
                masked_number="****8901"
            )
        ]
        
        holdings = {
            "acc_brokerage_1": [
                HoldingDTO(
                    symbol="AAPL",
                    security_name="Apple Inc.",
                    security_type=SecurityType.EQUITY,
                    quantity=50.0,
                    price=195.50,
                    value=9775.00,
                    cost_basis_total=8500.00,
                    cost_basis_per_unit=170.00
                ),
                HoldingDTO(
                    symbol="VTI",
                    security_name="Vanguard Total Stock Market ETF",
                    security_type=SecurityType.ETF,
                    quantity=100.0,
                    price=258.30,
                    value=25830.00,
                    cost_basis_total=22000.00,
                    cost_basis_per_unit=220.00
                )
            ],
            "acc_retirement_1": [
                HoldingDTO(
                    symbol="VXUS",
                    security_name="Vanguard Total International Stock ETF",
                    security_type=SecurityType.ETF,
                    quantity=150.0,
                    price=62.45,
                    value=9367.50,
                    cost_basis_total=8250.00,
                    cost_basis_per_unit=55.00
                ),
                HoldingDTO(
                    symbol="BND",
                    security_name="Vanguard Total Bond Market ETF",
                    security_type=SecurityType.ETF,
                    quantity=200.0,
                    price=72.80,
                    value=14560.00,
                    cost_basis_total=15000.00,
                    cost_basis_per_unit=75.00
                )
            ]
        }
        
        transactions = {
            "acc_brokerage_1": [
                TransactionDTO(
                    external_id="txn_plaid_001",
                    transaction_type=TransactionType.BUY,
                    posted_at=(datetime.utcnow() - timedelta(days=5)).isoformat() + "Z",
                    amount=-1955.00,
                    description="Buy AAPL",
                    symbol="AAPL",
                    security_type=SecurityType.EQUITY,
                    quantity=10.0,
                    price=195.50,
                    trade_date=(datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")
                ),
                TransactionDTO(
                    external_id="txn_plaid_002",
                    transaction_type=TransactionType.DIVIDEND,
                    posted_at=(datetime.utcnow() - timedelta(days=10)).isoformat() + "Z",
                    amount=45.00,
                    description="AAPL Dividend",
                    symbol="AAPL",
                    security_type=SecurityType.EQUITY
                )
            ],
            "acc_retirement_1": [
                TransactionDTO(
                    external_id="txn_plaid_003",
                    transaction_type=TransactionType.DEPOSIT,
                    posted_at=(datetime.utcnow() - timedelta(days=15)).isoformat() + "Z",
                    amount=6500.00,
                    description="IRA Contribution 2024"
                )
            ]
        }
        
        return SyncResult(
            success=True,
            accounts=accounts,
            holdings=holdings,
            transactions=transactions,
            raw_data={
                "source": "plaid_mock",
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "accounts_count": len(accounts),
                "holdings_count": sum(len(h) for h in holdings.values()),
                "transactions_count": sum(len(t) for t in transactions.values())
            }
        )
    
    def health_check(self, auth_data: Dict[str, Any]) -> HealthCheckResult:
        """
        Check if the connection is healthy.
        
        In production, this would call:
            plaid.item_get() and check for errors
        """
        access_token = auth_data.get("access_token")
        
        if not access_token:
            return HealthCheckResult(
                healthy=False,
                needs_reauth=True,
                message="Missing access token",
                error_code="MISSING_TOKEN"
            )
        
        # Mock: always healthy for placeholder
        return HealthCheckResult(
            healthy=True,
            needs_reauth=False,
            message="Connection is healthy"
        )
