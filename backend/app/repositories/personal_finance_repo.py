from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

from app.schemas.personal_finance import (
    InstitutionCreateRequest, InstitutionUpdateRequest,
    ConnectionCreateRequest, ConnectionUpdateRequest,
    AccountCreateRequest, AccountUpdateRequest,
    SecurityCreateRequest, SecurityUpdateRequest,
    HoldingCreateRequest, HoldingUpdateRequest,
    TransactionCreateRequest, TransactionUpdateRequest,
    SyncJobCreateRequest, SyncJobUpdateRequest,
    FileImportRequest, InstitutionListRequest,
    ConnectionListRequest, AccountListRequest,
    HoldingListRequest, TransactionListRequest,
    SyncJobListRequest, SourceType, ConnectionStatus,
    AccountType, AccountSubtype, SecurityType,
    TransactionType, SyncMode, SyncStatus
)


class InstitutionRepository(Protocol):
    """Repository interface for institution operations"""
    
    async def create_institution(self, institution_data: InstitutionCreateRequest) -> int:
        """Create a new institution and return its ID"""
        ...
    
    async def get_institution_by_id(self, institution_id: int) -> Optional[Dict[str, Any]]:
        """Get a single institution by ID"""
        ...
    
    async def get_institution_by_brand_key(self, brand_key: str) -> Optional[Dict[str, Any]]:
        """Get a single institution by brand key"""
        ...
    
    async def get_all_institutions(self, request: InstitutionListRequest) -> List[Dict[str, Any]]:
        """Get all institutions with optional filters"""
        ...
    
    async def update_institution(self, institution_id: int, updates: InstitutionUpdateRequest) -> bool:
        """Update an institution"""
        ...
    
    async def delete_institution(self, institution_id: int) -> bool:
        """Delete an institution"""
        ...
    
    async def search_institutions(self, query: str) -> List[Dict[str, Any]]:
        """Search institutions by name or brand key"""
        ...


class ConnectionRepository(Protocol):
    """Repository interface for connection operations"""
    
    async def create_connection(self, connection_data: ConnectionCreateRequest) -> int:
        """Create a new connection and return its ID"""
        ...
    
    async def get_connection_by_id(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Get a single connection by ID"""
        ...
    
    async def get_all_connections(self, request: ConnectionListRequest) -> List[Dict[str, Any]]:
        """Get all connections with optional filters"""
        ...
    
    async def update_connection(self, connection_id: int, updates: ConnectionUpdateRequest) -> bool:
        """Update a connection"""
        ...
    
    async def delete_connection(self, connection_id: int) -> bool:
        """Delete a connection"""
        ...
    
    async def update_connection_status(self, connection_id: int, status: ConnectionStatus) -> bool:
        """Update connection status"""
        ...
    
    async def update_connection_sync_time(self, connection_id: int, synced_at: datetime, next_sync: Optional[datetime] = None) -> bool:
        """Update connection sync time"""
        ...
    
    async def update_connection_auth(self, connection_id: int, auth_data: Dict[str, Any]) -> bool:
        """Update connection authentication data"""
        ...
    
    async def get_connections_needing_reauth(self) -> List[Dict[str, Any]]:
        """Get connections that need re-authentication"""
        ...


class AccountRepository(Protocol):
    """Repository interface for account operations"""
    
    async def create_account(self, account_data: AccountCreateRequest) -> int:
        """Create a new account and return its ID"""
        ...
    
    async def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get a single account by ID"""
        ...
    
    async def get_accounts_by_connection(self, connection_id: int) -> List[Dict[str, Any]]:
        """Get all accounts for a connection"""
        ...
    
    async def get_all_accounts(self, request: AccountListRequest) -> List[Dict[str, Any]]:
        """Get all accounts with optional filters"""
        ...
    
    async def update_account(self, account_id: int, updates: AccountUpdateRequest) -> bool:
        """Update an account"""
        ...
    
    async def delete_account(self, account_id: int) -> bool:
        """Delete an account"""
        ...
    
    async def get_account_total_value(self, account_id: int) -> Optional[float]:
        """Get total market value of all holdings in an account"""
        ...
    
    async def search_accounts(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search accounts by name or institution"""
        ...


class SecurityRepository(Protocol):
    """Repository interface for security operations"""
    
    async def create_security(self, security_data: SecurityCreateRequest) -> int:
        """Create a new security and return its ID"""
        ...
    
    async def get_security_by_id(self, security_id: int) -> Optional[Dict[str, Any]]:
        """Get a single security by ID"""
        ...
    
    async def get_security_by_symbol(self, symbol: str, security_type: Optional[SecurityType] = None) -> Optional[Dict[str, Any]]:
        """Get a single security by symbol and optional type"""
        ...
    
    async def get_all_securities(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all securities with pagination"""
        ...
    
    async def update_security(self, security_id: int, updates: SecurityUpdateRequest) -> bool:
        """Update a security"""
        ...
    
    async def delete_security(self, security_id: int) -> bool:
        """Delete a security"""
        ...
    
    async def search_securities(self, query: str, security_type: Optional[SecurityType] = None) -> List[Dict[str, Any]]:
        """Search securities by symbol or name"""
        ...
    
    async def get_popular_securities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most frequently traded securities"""
        ...


class HoldingRepository(Protocol):
    """Repository interface for holding operations"""
    
    async def create_holding(self, holding_data: HoldingCreateRequest) -> int:
        """Create a new holding and return its ID"""
        ...
    
    async def get_holding_by_id(self, holding_id: int) -> Optional[Dict[str, Any]]:
        """Get a single holding by ID"""
        ...
    
    async def get_holdings_by_account(self, account_id: int) -> List[Dict[str, Any]]:
        """Get all holdings for an account"""
        ...
    
    async def get_all_holdings(self, request: HoldingListRequest) -> List[Dict[str, Any]]:
        """Get all holdings with optional filters"""
        ...
    
    async def update_holding(self, holding_id: int, updates: HoldingUpdateRequest) -> bool:
        """Update a holding"""
        ...
    
    async def delete_holding(self, holding_id: int) -> bool:
        """Delete a holding"""
        ...
    
    async def upsert_holding(self, account_id: int, security_id: int, quantity: float, cost_basis: float, market_value: float, currency: str = "USD") -> int:
        """Create or update a holding (upsert operation)"""
        ...
    
    async def get_portfolio_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get portfolio summary statistics"""
        ...
    
    async def get_holdings_by_security(self, security_id: int) -> List[Dict[str, Any]]:
        """Get all holdings for a security across all accounts"""
        ...


class TransactionRepository(Protocol):
    """Repository interface for transaction operations"""
    
    async def create_transaction(self, transaction_data: TransactionCreateRequest) -> int:
        """Create a new transaction and return its ID"""
        ...
    
    async def get_transaction_by_id(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Get a single transaction by ID"""
        ...
    
    async def get_transactions_by_account(self, account_id: int, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all transactions for an account"""
        ...
    
    async def get_all_transactions(self, request: TransactionListRequest) -> List[Dict[str, Any]]:
        """Get all transactions with optional filters"""
        ...
    
    async def update_transaction(self, transaction_id: int, updates: TransactionUpdateRequest) -> bool:
        """Update a transaction"""
        ...
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        ...
    
    async def upsert_transaction(self, transaction_data: TransactionCreateRequest) -> int:
        """Create or update a transaction (upsert operation)"""
        ...
    
    async def search_transactions(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search transactions by description, category, or symbol"""
        ...
    
    async def get_transaction_statistics(self, account_id: Optional[int] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get transaction statistics"""
        ...


class SyncJobRepository(Protocol):
    """Repository interface for sync job operations"""
    
    async def create_sync_job(self, job_data: SyncJobCreateRequest) -> int:
        """Create a new sync job and return its ID"""
        ...
    
    async def get_sync_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a single sync job by ID"""
        ...
    
    async def get_sync_jobs_by_connection(self, connection_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all sync jobs for a connection"""
        ...
    
    async def get_all_sync_jobs(self, request: SyncJobListRequest) -> List[Dict[str, Any]]:
        """Get all sync jobs with optional filters"""
        ...
    
    async def update_sync_job(self, job_id: int, updates: SyncJobUpdateRequest) -> bool:
        """Update a sync job"""
        ...
    
    async def delete_sync_job(self, job_id: int) -> bool:
        """Delete a sync job"""
        ...
    
    async def get_pending_sync_jobs(self) -> List[Dict[str, Any]]:
        """Get all pending sync jobs"""
        ...
    
    async def get_running_sync_jobs(self) -> List[Dict[str, Any]]:
        """Get all running sync jobs"""
        ...


class FileImportRepository(Protocol):
    """Repository interface for file import operations"""
    
    async def process_file_upload(self, file_data: bytes, file_type: str, request: FileImportRequest) -> Dict[str, Any]:
        """Process uploaded file and import data"""
        ...
    
    async def parse_csv_file(self, file_data: bytes, mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Parse CSV file data"""
        ...
    
    async def parse_ofx_file(self, file_data: bytes) -> Dict[str, Any]:
        """Parse OFX/QFX file data"""
        ...
    
    async def validate_import_data(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate imported data before processing"""
        ...


class PersonalFinanceAnalyticsRepository(Protocol):
    """Repository interface for personal finance analytics"""
    
    async def get_portfolio_performance(self, user_id: Optional[str] = None, period_days: int = 365) -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        ...
    
    async def get_account_performance(self, account_id: int, period_days: int = 365) -> Dict[str, Any]:
        """Get account performance metrics"""
        ...
    
    async def get_security_performance(self, security_id: int, period_days: int = 365) -> Dict[str, Any]:
        """Get security performance metrics"""
        ...
    
    async def get_asset_allocation(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get asset allocation breakdown"""
        ...
    
    async def get_income_expense_analysis(self, user_id: Optional[str] = None, period_days: int = 365) -> Dict[str, Any]:
        """Get income and expense analysis"""
        ...
    
    async def get_transaction_categories(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get transaction categories with spending"""
        ...
    
    async def get_monthly_summary(self, user_id: Optional[str] = None, months: int = 12) -> Dict[str, Any]:
        """Get monthly financial summary"""
        ...


class PersonalFinanceIntegrationRepository(Protocol):
    """Repository interface for personal finance integration operations"""
    
    async def sync_connection_data(self, connection_id: int, sync_mode: SyncMode = SyncMode.INCREMENTAL) -> Dict[str, Any]:
        """Sync data from external connection"""
        ...
    
    async def test_connection(self, connection_id: int) -> Dict[str, Any]:
        """Test connection connectivity and authentication"""
        ...
    
    async def refresh_connection_token(self, connection_id: int) -> Dict[str, Any]:
        """Refresh connection authentication token"""
        ...
    
    async def get_connection_status(self, connection_id: int) -> Dict[str, Any]:
        """Get detailed connection status"""
        ...
    
    async def trigger_manual_sync(self, connection_id: int, sync_mode: SyncMode = SyncMode.INCREMENTAL) -> Dict[str, Any]:
        """Trigger manual sync for a connection"""
        ...
    
    async def get_sync_history(self, connection_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sync history for a connection"""
        ...
