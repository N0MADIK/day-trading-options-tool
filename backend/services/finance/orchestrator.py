"""
Sync Orchestrator

Central sync engine that coordinates data fetches, normalization, and storage.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from .models import (
    SourceType, SyncMode, SyncStatus, ConnectionStatus,
    AccountType, AccountSubtype, SecurityType, TransactionType
)
from .connectors import (
    BaseConnector, ConnectorRegistry, SyncResult, 
    AccountDTO, HoldingDTO, TransactionDTO
)
from .database import (
    get_connection_by_id, update_connection_status, update_connection_sync_time,
    upsert_account, upsert_security, upsert_holding, upsert_transaction,
    record_raw_event, create_sync_job, update_sync_job,
    get_accounts_by_connection, get_institution_by_id
)
from .encryption import decrypt_auth_blob

# Import and register connectors
from .connector_snaptrade import SnapTradeConnector
from .connector_robinhood import RobinhoodCryptoConnector
from .connector_file_import import FileImportConnector


def register_connectors():
    """Register all available connectors."""
    ConnectorRegistry.register(SnapTradeConnector())
    ConnectorRegistry.register(RobinhoodCryptoConnector())
    ConnectorRegistry.register(FileImportConnector())


# Register on module load
register_connectors()


class SyncOrchestrator:
    """
    Orchestrates sync operations for financial connections.
    
    Responsibilities:
    1. Fetch data from connectors
    2. Normalize and validate data
    3. Upsert to database
    4. Record raw events
    5. Update sync status and metrics
    """
    
    def __init__(self):
        pass
    
    def sync_connection(
        self,
        connection_id: int,
        mode: SyncMode = SyncMode.INCREMENTAL,
        triggered_by: str = "USER"
    ) -> Dict[str, Any]:
        """
        Run a sync for a connection.
        
        Args:
            connection_id: ID of the connection to sync
            mode: INITIAL or INCREMENTAL sync
            triggered_by: USER or SCHEDULE
            
        Returns:
            Dict with sync results and metrics
        """
        # Get connection
        connection = get_connection_by_id(connection_id)
        if not connection:
            return {
                "success": False,
                "error": f"Connection {connection_id} not found"
            }
        
        # Get connector
        connector = ConnectorRegistry.get(connection.source_type)
        if not connector:
            return {
                "success": False,
                "error": f"No connector for source type: {connection.source_type}"
            }
        
        # Create sync job
        job_id = create_sync_job(connection_id, mode, triggered_by)
        
        try:
            # Decrypt auth data
            auth_data = {}
            if connection.auth_blob_encrypted:
                decrypted = decrypt_auth_blob(connection.auth_blob_encrypted)
                if decrypted:
                    auth_data = json.loads(decrypted)
            
            # Run sync
            result = connector.sync_connection(
                connection_id=connection_id,
                auth_data=auth_data,
                mode=mode,
                last_synced_at=connection.last_synced_at
            )
            
            if not result.success:
                # Update job as failed
                update_sync_job(
                    job_id,
                    SyncStatus.FAILED,
                    error_summary="; ".join(result.errors)
                )
                
                # Check for auth errors
                if any("auth" in e.lower() or "token" in e.lower() for e in result.errors):
                    update_connection_status(
                        connection_id,
                        ConnectionStatus.NEEDS_REAUTH,
                        error_message=result.errors[0] if result.errors else "Authentication error"
                    )
                else:
                    update_connection_status(
                        connection_id,
                        ConnectionStatus.ERROR,
                        error_message=result.errors[0] if result.errors else "Sync failed"
                    )
                
                return {
                    "success": False,
                    "job_id": job_id,
                    "errors": result.errors
                }
            
            # Process results
            metrics = self._process_sync_result(connection_id, result, connection.source_type)
            
            # Update sync job
            update_sync_job(
                job_id,
                SyncStatus.SUCCESS,
                accounts_count=metrics["accounts"],
                holdings_count=metrics["holdings"],
                transactions_count=metrics["transactions"]
            )
            
            # Update connection
            update_connection_status(connection_id, ConnectionStatus.ACTIVE)
            update_connection_sync_time(connection_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "metrics": metrics
            }
            
        except Exception as e:
            # Update job as failed
            update_sync_job(job_id, SyncStatus.FAILED, error_summary=str(e))
            update_connection_status(
                connection_id,
                ConnectionStatus.ERROR,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e)
            }
    
    def _process_sync_result(
        self,
        connection_id: int,
        result: SyncResult,
        source_type: SourceType
    ) -> Dict[str, int]:
        """
        Process sync result and upsert data to database.
        
        Returns:
            Dict with count metrics
        """
        metrics = {
            "accounts": 0,
            "securities": 0,
            "holdings": 0,
            "transactions": 0
        }
        
        # Map external account IDs to database IDs
        account_id_map: Dict[str, int] = {}
        
        # Process accounts
        for account_dto in result.accounts:
            db_account_id = upsert_account(
                connection_id=connection_id,
                external_account_id=account_dto.external_id,
                name=account_dto.name,
                account_type=account_dto.account_type,
                account_subtype=account_dto.account_subtype,
                currency=account_dto.currency,
                masked_number=account_dto.masked_number
            )
            account_id_map[account_dto.external_id] = db_account_id
            metrics["accounts"] += 1
        
        # Process holdings (per account)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        for ext_account_id, holdings in result.holdings.items():
            db_account_id = account_id_map.get(ext_account_id)
            if not db_account_id:
                continue
            
            for holding_dto in holdings:
                # Upsert security first
                security_id = upsert_security(
                    symbol=holding_dto.symbol,
                    security_type=holding_dto.security_type,
                    name=holding_dto.security_name,
                    cusip=holding_dto.cusip,
                    isin=holding_dto.isin
                )
                metrics["securities"] += 1
                
                # Upsert holding
                upsert_holding(
                    account_id=db_account_id,
                    security_id=security_id,
                    quantity=holding_dto.quantity,
                    as_of=today,
                    cost_basis_total=holding_dto.cost_basis_total,
                    cost_basis_per_unit=holding_dto.cost_basis_per_unit,
                    price=holding_dto.price,
                    value=holding_dto.value
                )
                metrics["holdings"] += 1
        
        # Process transactions (per account)
        for ext_account_id, transactions in result.transactions.items():
            db_account_id = account_id_map.get(ext_account_id)
            if not db_account_id:
                continue
            
            for txn_dto in transactions:
                # Upsert security if present
                security_id = None
                if txn_dto.symbol:
                    security_id = upsert_security(
                        symbol=txn_dto.symbol,
                        security_type=txn_dto.security_type or SecurityType.EQUITY,
                        name=txn_dto.symbol  # Use symbol as name fallback
                    )
                
                # Upsert transaction
                upsert_transaction(
                    account_id=db_account_id,
                    transaction_type=txn_dto.transaction_type,
                    posted_at=txn_dto.posted_at,
                    amount=txn_dto.amount,
                    description=txn_dto.description,
                    security_id=security_id,
                    external_txn_id=txn_dto.external_id,
                    trade_date=txn_dto.trade_date,
                    settle_date=txn_dto.settle_date,
                    quantity=txn_dto.quantity,
                    price=txn_dto.price,
                    currency=txn_dto.currency,
                    raw_category=txn_dto.raw_category
                )
                metrics["transactions"] += 1
        
        # Record raw event
        if result.raw_data:
            record_raw_event(
                connection_id=connection_id,
                source_type=source_type,
                event_type="sync_result",
                payload=result.raw_data
            )
        
        return metrics
    
    def process_file_upload(
        self,
        connection_id: int,
        file_path: str,
        file_type: str,
        institution: str = "generic"
    ) -> Dict[str, Any]:
        """
        Process an uploaded file for a file import connection.
        
        Args:
            connection_id: The connection ID
            file_path: Path to the uploaded file
            file_type: File format (ofx, qfx, csv)
            institution: Institution for CSV mapping
            
        Returns:
            Dict with processing results
        """
        connection = get_connection_by_id(connection_id)
        if not connection:
            return {"success": False, "error": "Connection not found"}
        
        if connection.source_type != SourceType.FILE_IMPORT:
            return {"success": False, "error": "Connection is not a file import type"}
        
        # Get file import connector
        connector = ConnectorRegistry.get(SourceType.FILE_IMPORT)
        if not connector or not isinstance(connector, FileImportConnector):
            return {"success": False, "error": "File import connector not available"}
        
        # Create sync job
        job_id = create_sync_job(connection_id, SyncMode.INITIAL, "FILE_UPLOAD")
        
        try:
            # Process file
            result = connector.process_upload(connection_id, file_path, file_type, institution)
            
            if not result.success:
                update_sync_job(job_id, SyncStatus.FAILED, error_summary="; ".join(result.errors))
                return {
                    "success": False,
                    "job_id": job_id,
                    "errors": result.errors
                }
            
            # Process results
            metrics = self._process_sync_result(connection_id, result, SourceType.FILE_IMPORT)
            
            # Update job
            update_sync_job(
                job_id,
                SyncStatus.SUCCESS,
                accounts_count=metrics["accounts"],
                holdings_count=metrics["holdings"],
                transactions_count=metrics["transactions"]
            )
            
            # Update connection
            update_connection_sync_time(connection_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "metrics": metrics
            }
            
        except Exception as e:
            update_sync_job(job_id, SyncStatus.FAILED, error_summary=str(e))
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e)
            }


# Singleton instance
orchestrator = SyncOrchestrator()


def sync_connection(connection_id: int, mode: SyncMode = SyncMode.INCREMENTAL, triggered_by: str = "USER") -> Dict[str, Any]:
    """Convenience function to sync a connection."""
    return orchestrator.sync_connection(connection_id, mode, triggered_by)


def process_file_upload(connection_id: int, file_path: str, file_type: str, institution: str = "generic") -> Dict[str, Any]:
    """Convenience function to process a file upload."""
    return orchestrator.process_file_upload(connection_id, file_path, file_type, institution)
