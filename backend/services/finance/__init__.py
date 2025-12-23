# Finance module
"""
Personal Finance Tracker - Core Module

This module provides:
- Database models and operations for financial data
- Connector framework for aggregators (Plaid), Robinhood Crypto, and file imports
- Parsers for OFX/QFX and CSV files
- Sync orchestration
"""

from .models import (
    SourceType, ConnectionStatus, AccountType, AccountSubtype,
    SecurityType, TransactionType, SyncMode, SyncStatus,
    Institution, Connection, Account, Security, Holding, 
    Transaction, RawEvent, SyncJob
)

from .database import (
    init_finance_db,
    get_all_institutions, get_institution_by_id, get_institution_by_brand_key,
    create_connection, get_all_connections, get_connection_by_id,
    update_connection_status, update_connection_sync_time, update_connection_auth,
    upsert_account, get_accounts_by_connection, get_account_by_id,
    upsert_security, get_security_by_symbol,
    upsert_holding, get_holdings_by_account, get_account_total_value,
    upsert_transaction, get_transactions_by_account,
    record_raw_event, create_sync_job, update_sync_job, get_sync_jobs_by_connection
)

from .encryption import encrypt_auth_blob, decrypt_auth_blob, generate_new_key

from .connectors import (
    BaseConnector, ConnectorRegistry, 
    LinkSessionResult, ExchangeResult, SyncResult, HealthCheckResult,
    AccountDTO, HoldingDTO, TransactionDTO
)

from .orchestrator import sync_connection, process_file_upload

__all__ = [
    # Enums
    "SourceType", "ConnectionStatus", "AccountType", "AccountSubtype",
    "SecurityType", "TransactionType", "SyncMode", "SyncStatus",
    # Models
    "Institution", "Connection", "Account", "Security", "Holding",
    "Transaction", "RawEvent", "SyncJob",
    # Database
    "init_finance_db",
    "get_all_institutions", "get_institution_by_id", "get_institution_by_brand_key",
    "create_connection", "get_all_connections", "get_connection_by_id",
    "update_connection_status", "update_connection_sync_time", "update_connection_auth",
    "upsert_account", "get_accounts_by_connection", "get_account_by_id",
    "upsert_security", "get_security_by_symbol",
    "upsert_holding", "get_holdings_by_account", "get_account_total_value",
    "upsert_transaction", "get_transactions_by_account",
    "record_raw_event", "create_sync_job", "update_sync_job", "get_sync_jobs_by_connection",
    # Encryption
    "encrypt_auth_blob", "decrypt_auth_blob", "generate_new_key",
    # Connectors
    "BaseConnector", "ConnectorRegistry",
    "LinkSessionResult", "ExchangeResult", "SyncResult", "HealthCheckResult",
    "AccountDTO", "HoldingDTO", "TransactionDTO",
    # Orchestrator
    "sync_connection", "process_file_upload"
]
