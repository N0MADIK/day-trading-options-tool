"""
File Import Connector

Connector for importing financial data from QFX/OFX/CSV files.
Handles Fidelity, Vanguard, and other brokerage exports.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from .models import (
    SourceType, SyncMode, AccountType, AccountSubtype, 
    SecurityType, TransactionType
)
from .connectors import (
    BaseConnector, LinkSessionResult, ExchangeResult, SyncResult,
    HealthCheckResult, AccountDTO, HoldingDTO, TransactionDTO
)


class FileImportConnector(BaseConnector):
    """
    Connector for file-based imports (QFX/OFX/CSV).
    
    Supports:
    - Fidelity exports
    - Vanguard exports
    - Generic OFX/QFX files
    - Generic CSV files
    """
    
    source_type = SourceType.FILE_IMPORT
    
    def __init__(self):
        # Directory for uploaded files
        self.upload_dir = Path(__file__).parent.parent.parent / "data" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def create_link_session(self, user_id: str, **kwargs) -> LinkSessionResult:
        """
        For file imports, this just returns instructions for the user.
        No external auth flow required.
        """
        institution = kwargs.get("institution", "generic")
        
        instructions = {
            "fidelity": "Log into Fidelity.com, go to Accounts & Trade > Activity & Orders, click Download",
            "vanguard": "Log into Vanguard.com, go to My Accounts, select Download Transactions",
            "generic": "Export transactions from your brokerage in QFX, OFX, or CSV format"
        }
        
        return LinkSessionResult(
            success=True,
            session_id=f"file_import_{institution}_{user_id}",
            link_url=None,
            link_token=None,
            expires_at=None  # No expiry for file imports
        )
    
    def exchange_link_artifact(self, user_id: str, artifact: Dict[str, Any]) -> ExchangeResult:
        """
        For file imports, store the institution and account metadata.
        No tokens to exchange.
        """
        institution = artifact.get("institution", "generic")
        account_name = artifact.get("account_name", "Imported Account")
        
        return ExchangeResult(
            success=True,
            auth_data={
                "institution": institution,
                "account_name": account_name,
                "import_type": "file",
                "created_at": datetime.utcnow().isoformat() + "Z"
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
        For file imports, sync is triggered by file upload.
        This returns any previously imported data.
        """
        institution = auth_data.get("institution", "generic")
        account_name = auth_data.get("account_name", "Imported Account")
        
        # Return the account metadata
        account_type = AccountType.BROKERAGE
        account_subtype = AccountSubtype.UNKNOWN
        
        # Infer account type from name
        name_lower = account_name.lower()
        if "roth" in name_lower:
            account_type = AccountType.RETIREMENT
            account_subtype = AccountSubtype.ROTH_IRA
        elif "ira" in name_lower:
            account_type = AccountType.RETIREMENT
            account_subtype = AccountSubtype.TRAD_IRA
        elif "401" in name_lower:
            account_type = AccountType.RETIREMENT
            account_subtype = AccountSubtype.K401
        
        accounts = [
            AccountDTO(
                external_id=f"file_{institution}_{connection_id}",
                name=account_name,
                account_type=account_type,
                account_subtype=account_subtype,
                currency="USD"
            )
        ]
        
        return SyncResult(
            success=True,
            accounts=accounts,
            holdings={},
            transactions={},
            raw_data={
                "source": "file_import",
                "institution": institution,
                "fetched_at": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def process_upload(
        self,
        connection_id: int,
        file_path: str,
        file_type: str,  # "ofx", "qfx", "csv"
        institution: str = "generic"
    ) -> SyncResult:
        """
        Process an uploaded file and extract transactions/holdings.
        
        Args:
            connection_id: The connection ID
            file_path: Path to the uploaded file
            file_type: File format (ofx, qfx, csv)
            institution: Institution for CSV mapping
            
        Returns:
            SyncResult with parsed data
        """
        # Import parsers here to avoid circular imports
        from .parser_ofx import parse_ofx_file
        from .parser_csv import parse_csv_file
        
        try:
            if file_type in ("ofx", "qfx"):
                result = parse_ofx_file(file_path)
            elif file_type == "csv":
                result = parse_csv_file(file_path, institution)
            else:
                return SyncResult(
                    success=False,
                    errors=[f"Unsupported file type: {file_type}"]
                )
            
            return result
            
        except Exception as e:
            return SyncResult(
                success=False,
                errors=[f"Failed to parse file: {str(e)}"]
            )
    
    def health_check(self, auth_data: Dict[str, Any]) -> HealthCheckResult:
        """
        File imports don't have auth to check.
        Always return healthy.
        """
        return HealthCheckResult(
            healthy=True,
            needs_reauth=False,
            message="File import connections don't require authentication"
        )
