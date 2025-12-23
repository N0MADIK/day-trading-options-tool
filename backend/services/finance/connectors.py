"""
Base Connector Interface

Abstract base class defining the connector contract for all financial data sources.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from .models import (
    Account, Holding, Transaction, Security,
    SourceType, SyncMode, AccountType, AccountSubtype, SecurityType, TransactionType
)


@dataclass
class LinkSessionResult:
    """Result from creating a link session."""
    success: bool
    session_id: Optional[str] = None
    link_url: Optional[str] = None
    link_token: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExchangeResult:
    """Result from exchanging link artifact for auth credentials."""
    success: bool
    auth_data: Optional[Dict[str, Any]] = None  # To be encrypted before storage
    error: Optional[str] = None


@dataclass
class AccountDTO:
    """Data transfer object for account data from connectors."""
    external_id: str
    name: str
    account_type: AccountType
    account_subtype: AccountSubtype = AccountSubtype.UNKNOWN
    currency: str = "USD"
    masked_number: Optional[str] = None


@dataclass
class HoldingDTO:
    """Data transfer object for holding data from connectors."""
    symbol: str
    security_name: str
    security_type: SecurityType
    quantity: float
    price: Optional[float] = None
    value: Optional[float] = None
    cost_basis_total: Optional[float] = None
    cost_basis_per_unit: Optional[float] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None


@dataclass
class TransactionDTO:
    """Data transfer object for transaction data from connectors."""
    external_id: Optional[str]  # Can be None, will use dedupe key
    transaction_type: TransactionType
    posted_at: str
    amount: float
    description: str
    symbol: Optional[str] = None
    security_type: Optional[SecurityType] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    trade_date: Optional[str] = None
    settle_date: Optional[str] = None
    currency: str = "USD"
    raw_category: Optional[str] = None


@dataclass
class SyncResult:
    """Result from a sync operation."""
    success: bool
    accounts: List[AccountDTO] = field(default_factory=list)
    holdings: Dict[str, List[HoldingDTO]] = field(default_factory=dict)  # account_id -> holdings
    transactions: Dict[str, List[TransactionDTO]] = field(default_factory=dict)  # account_id -> txns
    errors: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None  # For raw_events storage


@dataclass
class HealthCheckResult:
    """Result from health check."""
    healthy: bool
    needs_reauth: bool = False
    message: Optional[str] = None
    error_code: Optional[str] = None


class BaseConnector(ABC):
    """
    Abstract base class for financial data connectors.
    
    All connectors must implement these methods to integrate with the sync pipeline.
    """
    
    source_type: SourceType
    
    @abstractmethod
    def create_link_session(self, user_id: str, **kwargs) -> LinkSessionResult:
        """
        Create a link session for the user to connect their account.
        
        Args:
            user_id: The user initiating the link
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LinkSessionResult with session info or error
        """
        pass
    
    @abstractmethod
    def exchange_link_artifact(self, user_id: str, artifact: Dict[str, Any]) -> ExchangeResult:
        """
        Exchange a link artifact (public token, auth code, etc.) for auth credentials.
        
        Args:
            user_id: The user who completed linking
            artifact: Provider-specific artifact (e.g., public_token, auth_code)
            
        Returns:
            ExchangeResult with auth data to be encrypted and stored
        """
        pass
    
    @abstractmethod
    def sync_connection(
        self, 
        connection_id: int, 
        auth_data: Dict[str, Any],
        mode: SyncMode = SyncMode.INCREMENTAL,
        last_synced_at: Optional[str] = None
    ) -> SyncResult:
        """
        Sync data from the connected institution.
        
        Args:
            connection_id: ID of the connection to sync
            auth_data: Decrypted auth credentials
            mode: INITIAL or INCREMENTAL sync
            last_synced_at: Timestamp of last successful sync (for incremental)
            
        Returns:
            SyncResult with all fetched data
        """
        pass
    
    @abstractmethod
    def health_check(self, auth_data: Dict[str, Any]) -> HealthCheckResult:
        """
        Check if the connection is healthy and auth is valid.
        
        Args:
            auth_data: Decrypted auth credentials
            
        Returns:
            HealthCheckResult indicating status
        """
        pass
    
    def list_accounts(
        self, 
        connection_id: int, 
        auth_data: Dict[str, Any]
    ) -> List[AccountDTO]:
        """
        List accounts from the connected institution.
        Default implementation uses sync_connection.
        """
        result = self.sync_connection(connection_id, auth_data, SyncMode.INCREMENTAL)
        return result.accounts
    
    def list_holdings(
        self, 
        connection_id: int, 
        auth_data: Dict[str, Any],
        account_external_id: str,
        cursor: Optional[str] = None
    ) -> List[HoldingDTO]:
        """
        List holdings for a specific account.
        Default implementation uses sync_connection.
        """
        result = self.sync_connection(connection_id, auth_data, SyncMode.INCREMENTAL)
        return result.holdings.get(account_external_id, [])
    
    def list_transactions(
        self,
        connection_id: int,
        auth_data: Dict[str, Any],
        account_external_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> List[TransactionDTO]:
        """
        List transactions for a specific account.
        Default implementation uses sync_connection.
        """
        result = self.sync_connection(connection_id, auth_data, SyncMode.INCREMENTAL)
        return result.transactions.get(account_external_id, [])


class ConnectorRegistry:
    """Registry of available connectors."""
    
    _connectors: Dict[SourceType, BaseConnector] = {}
    
    @classmethod
    def register(cls, connector: BaseConnector):
        """Register a connector instance."""
        cls._connectors[connector.source_type] = connector
    
    @classmethod
    def get(cls, source_type: SourceType) -> Optional[BaseConnector]:
        """Get a connector by source type."""
        return cls._connectors.get(source_type)
    
    @classmethod
    def get_all(cls) -> List[BaseConnector]:
        """Get all registered connectors."""
        return list(cls._connectors.values())
