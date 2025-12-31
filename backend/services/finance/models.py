"""
Finance Data Models

Normalized database schema for personal finance tracking.
Based on walkthrough_p2.md specifications.
"""
import sqlite3
import json
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


# ============================================================================
# ENUMS
# ============================================================================

class SourceType(str, Enum):
    AGGREGATOR = "AGGREGATOR"  # Deprecated (Plaid)
    SNAPTRADE = "SNAPTRADE"
    ROBINHOOD_CRYPTO = "ROBINHOOD_CRYPTO"
    FILE_IMPORT = "FILE_IMPORT"


class ConnectionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    NEEDS_REAUTH = "NEEDS_REAUTH"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


class AccountType(str, Enum):
    BROKERAGE = "BROKERAGE"
    RETIREMENT = "RETIREMENT"
    CASH = "CASH"
    CRYPTO = "CRYPTO"
    UNKNOWN = "UNKNOWN"


class AccountSubtype(str, Enum):
    TAXABLE = "TAXABLE"
    ROTH_IRA = "ROTH_IRA"
    TRAD_IRA = "TRAD_IRA"
    K401 = "401K"
    K403B = "403B"
    HSA = "HSA"
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CRYPTO = "CRYPTO"
    UNKNOWN = "UNKNOWN"


class SecurityType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    BOND = "BOND"
    CRYPTO = "CRYPTO"
    CASH = "CASH"
    OPTION = "OPTION"
    UNKNOWN = "UNKNOWN"


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    FEE = "FEE"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    SPLIT = "SPLIT"
    UNKNOWN = "UNKNOWN"


class SyncMode(str, Enum):
    INITIAL = "INITIAL"
    INCREMENTAL = "INCREMENTAL"


class SyncStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# ============================================================================
# DATA CLASSES (Models)
# ============================================================================

@dataclass
class Institution:
    """Financial institution (bank/brokerage)"""
    id: Optional[int] = None
    name: str = ""
    brand_key: str = ""  # e.g., "fidelity", "vanguard"
    source_type: SourceType = SourceType.AGGREGATOR
    logo_url: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "brand_key": self.brand_key,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "logo_url": self.logo_url,
            "created_at": self.created_at
        }


@dataclass
class Connection:
    """User's connection to an institution"""
    id: Optional[int] = None
    user_id: str = "default"  # Single-user for now
    institution_id: int = 0
    source_type: SourceType = SourceType.AGGREGATOR
    status: ConnectionStatus = ConnectionStatus.ACTIVE
    auth_blob_encrypted: Optional[str] = None  # Encrypted tokens/keys
    last_synced_at: Optional[str] = None
    next_sync_at: Optional[str] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "institution_id": self.institution_id,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "status": self.status.value if isinstance(self.status, ConnectionStatus) else self.status,
            "last_synced_at": self.last_synced_at,
            "next_sync_at": self.next_sync_at,
            "last_error_code": self.last_error_code,
            "last_error_message": self.last_error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class Account:
    """Financial account under a connection"""
    id: Optional[int] = None
    connection_id: int = 0
    external_account_id: str = ""  # ID from provider
    name: str = ""
    account_type: AccountType = AccountType.UNKNOWN
    account_subtype: AccountSubtype = AccountSubtype.UNKNOWN
    currency: str = "USD"
    institution_masked_number: Optional[str] = None  # e.g., "****1234"
    is_closed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "external_account_id": self.external_account_id,
            "name": self.name,
            "account_type": self.account_type.value if isinstance(self.account_type, AccountType) else self.account_type,
            "account_subtype": self.account_subtype.value if isinstance(self.account_subtype, AccountSubtype) else self.account_subtype,
            "currency": self.currency,
            "institution_masked_number": self.institution_masked_number,
            "is_closed": self.is_closed,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class Security:
    """Security/asset (stock, ETF, crypto, etc.)"""
    id: Optional[int] = None
    symbol: str = ""
    name: str = ""
    cusip: Optional[str] = None
    isin: Optional[str] = None
    security_type: SecurityType = SecurityType.UNKNOWN
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "cusip": self.cusip,
            "isin": self.isin,
            "security_type": self.security_type.value if isinstance(self.security_type, SecurityType) else self.security_type,
            "created_at": self.created_at
        }


@dataclass
class Holding:
    """Position/holding in an account"""
    id: Optional[int] = None
    account_id: int = 0
    security_id: int = 0
    quantity: float = 0.0
    cost_basis_total: Optional[float] = None
    cost_basis_per_unit: Optional[float] = None
    price: Optional[float] = None
    value: Optional[float] = None
    as_of: str = ""  # Date of this snapshot
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "security_id": self.security_id,
            "quantity": self.quantity,
            "cost_basis_total": self.cost_basis_total,
            "cost_basis_per_unit": self.cost_basis_per_unit,
            "price": self.price,
            "value": self.value,
            "as_of": self.as_of,
            "created_at": self.created_at
        }


@dataclass
class Transaction:
    """Financial transaction"""
    id: Optional[int] = None
    account_id: int = 0
    security_id: Optional[int] = None
    external_txn_id: Optional[str] = None  # OFX FITID or provider ID
    dedupe_key: Optional[str] = None  # Hash-based fallback ID
    transaction_type: TransactionType = TransactionType.UNKNOWN
    trade_date: Optional[str] = None
    settle_date: Optional[str] = None
    posted_at: str = ""
    quantity: Optional[float] = None
    price: Optional[float] = None
    amount: float = 0.0  # Signed: negative = outflow, positive = inflow
    currency: str = "USD"
    description: str = ""
    raw_category: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "security_id": self.security_id,
            "external_txn_id": self.external_txn_id,
            "dedupe_key": self.dedupe_key,
            "transaction_type": self.transaction_type.value if isinstance(self.transaction_type, TransactionType) else self.transaction_type,
            "trade_date": self.trade_date,
            "settle_date": self.settle_date,
            "posted_at": self.posted_at,
            "quantity": self.quantity,
            "price": self.price,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "raw_category": self.raw_category,
            "created_at": self.created_at
        }


@dataclass
class RawEvent:
    """Raw data from sync operations (for debugging/replay)"""
    id: Optional[int] = None
    connection_id: int = 0
    source_type: SourceType = SourceType.AGGREGATOR
    event_type: str = ""  # e.g., "accounts", "holdings", "transactions"
    payload_json: str = "{}"
    checksum: str = ""
    received_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "checksum": self.checksum,
            "received_at": self.received_at
        }


@dataclass
class SyncJob:
    """Record of a sync operation"""
    id: Optional[int] = None
    connection_id: int = 0
    triggered_by: str = "USER"  # USER or SCHEDULE
    mode: SyncMode = SyncMode.INITIAL
    status: SyncStatus = SyncStatus.PENDING
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    accounts_count: int = 0
    holdings_count: int = 0
    transactions_count: int = 0
    error_summary: Optional[str] = None
    attempt_count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "triggered_by": self.triggered_by,
            "mode": self.mode.value if isinstance(self.mode, SyncMode) else self.mode,
            "status": self.status.value if isinstance(self.status, SyncStatus) else self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "accounts_count": self.accounts_count,
            "holdings_count": self.holdings_count,
            "transactions_count": self.transactions_count,
            "error_summary": self.error_summary,
            "attempt_count": self.attempt_count
        }
