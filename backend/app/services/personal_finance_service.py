from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json

from app.repositories.personal_finance_repo import (
    InstitutionRepository, ConnectionRepository, AccountRepository,
    SecurityRepository, HoldingRepository, TransactionRepository,
    SyncJobRepository, FileImportRepository,
    PersonalFinanceAnalyticsRepository, PersonalFinanceIntegrationRepository
)
from app.repositories.sqlalchemy.personal_finance_repo import (
    SQLAlchemyInstitutionRepository, SQLAlchemyConnectionRepository,
    SQLAlchemyAccountRepository, SQLAlchemySecurityRepository,
    SQLAlchemyHoldingRepository, SQLAlchemyTransactionRepository,
    SQLAlchemySyncJobRepository, SQLAlchemyFileImportRepository,
    SQLAlchemyPersonalFinanceAnalyticsRepository,
    SQLAlchemyPersonalFinanceIntegrationRepository
)
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
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class PersonalFinanceService:
    """Service for personal finance operations"""
    
    def __init__(
        self,
        institution_repo: InstitutionRepository,
        connection_repo: ConnectionRepository,
        account_repo: AccountRepository,
        security_repo: SecurityRepository,
        holding_repo: HoldingRepository,
        transaction_repo: TransactionRepository,
        sync_job_repo: SyncJobRepository,
        file_import_repo: FileImportRepository,
        analytics_repo: PersonalFinanceAnalyticsRepository,
        integration_repo: PersonalFinanceIntegrationRepository
    ):
        self.institution_repo = institution_repo
        self.connection_repo = connection_repo
        self.account_repo = account_repo
        self.security_repo = security_repo
        self.holding_repo = holding_repo
        self.transaction_repo = transaction_repo
        self.sync_job_repo = sync_job_repo
        self.file_import_repo = file_import_repo
        self.analytics_repo = analytics_repo
        self.integration_repo = integration_repo
    
    # Institution Management
    async def create_institution(self, institution_data: InstitutionCreateRequest) -> Dict[str, Any]:
        """Create a new institution"""
        try:
            # Check if brand key already exists
            existing = await self.institution_repo.get_institution_by_brand_key(institution_data.brand_key)
            if existing:
                raise ConflictError(f"Institution with brand key '{institution_data.brand_key}' already exists")
            
            institution_id = await self.institution_repo.create_institution(institution_data)
            
            # Get created institution
            institution = await self.institution_repo.get_institution_by_id(institution_id)
            
            return {
                "success": True,
                "institution_id": institution_id,
                "institution": institution
            }
            
        except Exception as e:
            raise e
    
    async def get_institution_by_id(self, institution_id: int) -> Dict[str, Any]:
        """Get a single institution by ID"""
        try:
            institution = await self.institution_repo.get_institution_by_id(institution_id)
            
            if not institution:
                raise NotFoundError(f"Institution with ID {institution_id} not found")
            
            return {
                "success": True,
                "institution": institution
            }
            
        except Exception as e:
            raise e
    
    async def get_institution_by_brand_key(self, brand_key: str) -> Dict[str, Any]:
        """Get a single institution by brand key"""
        try:
            institution = await self.institution_repo.get_institution_by_brand_key(brand_key)
            
            if not institution:
                raise NotFoundError(f"Institution with brand key '{brand_key}' not found")
            
            return {
                "success": True,
                "institution": institution
            }
            
        except Exception as e:
            raise e
    
    async def list_institutions(self, request: InstitutionListRequest) -> Dict[str, Any]:
        """List institutions with optional filters"""
        try:
            institutions = await self.institution_repo.get_all_institutions(request)
            
            return {
                "success": True,
                "institutions": institutions,
                "total_count": len(institutions)
            }
            
        except Exception as e:
            raise e
    
    async def update_institution(self, institution_id: int, updates: InstitutionUpdateRequest) -> Dict[str, Any]:
        """Update an institution"""
        try:
            success = await self.institution_repo.update_institution(institution_id, updates)
            
            if not success:
                raise NotFoundError(f"Institution with ID {institution_id} not found")
            
            # Get updated institution
            institution = await self.institution_repo.get_institution_by_id(institution_id)
            
            return {
                "success": True,
                "institution": institution
            }
            
        except Exception as e:
            raise e
    
    async def delete_institution(self, institution_id: int) -> Dict[str, Any]:
        """Delete an institution"""
        try:
            success = await self.institution_repo.delete_institution(institution_id)
            
            if not success:
                raise NotFoundError(f"Institution with ID {institution_id} not found")
            
            return {
                "success": True,
                "message": f"Institution {institution_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def search_institutions(self, query: str) -> Dict[str, Any]:
        """Search institutions by name or brand key"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            institutions = await self.institution_repo.search_institutions(query.strip())
            
            return {
                "success": True,
                "institutions": institutions,
                "total_count": len(institutions)
            }
            
        except Exception as e:
            raise e
    
    # Connection Management
    async def create_connection(self, connection_data: ConnectionCreateRequest) -> Dict[str, Any]:
        """Create a new connection"""
        try:
            # Validate institution exists
            institution = await self.institution_repo.get_institution_by_id(connection_data.institution_id)
            if not institution:
                raise NotFoundError(f"Institution with ID {connection_data.institution_id} not found")
            
            connection_id = await self.connection_repo.create_connection(connection_data)
            
            # Get created connection
            connection = await self.connection_repo.get_connection_by_id(connection_id)
            
            return {
                "success": True,
                "connection_id": connection_id,
                "connection": connection
            }
            
        except Exception as e:
            raise e
    
    async def get_connection_by_id(self, connection_id: int) -> Dict[str, Any]:
        """Get a single connection by ID"""
        try:
            connection = await self.connection_repo.get_connection_by_id(connection_id)
            
            if not connection:
                raise NotFoundError(f"Connection with ID {connection_id} not found")
            
            return {
                "success": True,
                "connection": connection
            }
            
        except Exception as e:
            raise e
    
    async def list_connections(self, request: ConnectionListRequest) -> Dict[str, Any]:
        """List connections with optional filters"""
        try:
            connections = await self.connection_repo.get_all_connections(request)
            
            return {
                "success": True,
                "connections": connections,
                "total_count": len(connections)
            }
            
        except Exception as e:
            raise e
    
    async def update_connection(self, connection_id: int, updates: ConnectionUpdateRequest) -> Dict[str, Any]:
        """Update a connection"""
        try:
            success = await self.connection_repo.update_connection(connection_id, updates)
            
            if not success:
                raise NotFoundError(f"Connection with ID {connection_id} not found")
            
            # Get updated connection
            connection = await self.connection_repo.get_connection_by_id(connection_id)
            
            return {
                "success": True,
                "connection": connection
            }
            
        except Exception as e:
            raise e
    
    async def delete_connection(self, connection_id: int) -> Dict[str, Any]:
        """Delete a connection"""
        try:
            success = await self.connection_repo.delete_connection(connection_id)
            
            if not success:
                raise NotFoundError(f"Connection with ID {connection_id} not found")
            
            return {
                "success": True,
                "message": f"Connection {connection_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def test_connection(self, connection_id: int) -> Dict[str, Any]:
        """Test connection connectivity and authentication"""
        try:
            result = await self.integration_repo.test_connection(connection_id)
            
            return {
                "success": True,
                "test_result": result
            }
            
        except Exception as e:
            raise e
    
    async def trigger_sync(self, connection_id: int, sync_mode: SyncMode = SyncMode.INCREMENTAL) -> Dict[str, Any]:
        """Trigger manual sync for a connection"""
        try:
            result = await self.integration_repo.trigger_manual_sync(connection_id, sync_mode)
            
            # Update connection sync time
            await self.connection_repo.update_connection_sync_time(
                connection_id, 
                datetime.utcnow(),
                datetime.utcnow() + timedelta(hours=24)
            )
            
            return {
                "success": True,
                "sync_result": result
            }
            
        except Exception as e:
            raise e
    
    async def get_connections_needing_reauth(self) -> Dict[str, Any]:
        """Get connections that need re-authentication"""
        try:
            connections = await self.connection_repo.get_connections_needing_reauth()
            
            return {
                "success": True,
                "connections": connections,
                "total_count": len(connections)
            }
            
        except Exception as e:
            raise e
    
    # Account Management
    async def create_account(self, account_data: AccountCreateRequest) -> Dict[str, Any]:
        """Create a new account"""
        try:
            # Validate connection exists
            connection = await self.connection_repo.get_connection_by_id(account_data.connection_id)
            if not connection:
                raise NotFoundError(f"Connection with ID {account_data.connection_id} not found")
            
            account_id = await self.account_repo.create_account(account_data)
            
            # Get created account
            account = await self.account_repo.get_account_by_id(account_id)
            
            return {
                "success": True,
                "account_id": account_id,
                "account": account
            }
            
        except Exception as e:
            raise e
    
    async def get_account_by_id(self, account_id: int) -> Dict[str, Any]:
        """Get a single account by ID"""
        try:
            account = await self.account_repo.get_account_by_id(account_id)
            
            if not account:
                raise NotFoundError(f"Account with ID {account_id} not found")
            
            return {
                "success": True,
                "account": account
            }
            
        except Exception as e:
            raise e
    
    async def list_accounts(self, request: AccountListRequest) -> Dict[str, Any]:
        """List accounts with optional filters"""
        try:
            accounts = await self.account_repo.get_all_accounts(request)
            
            return {
                "success": True,
                "accounts": accounts,
                "total_count": len(accounts)
            }
            
        except Exception as e:
            raise e
    
    async def update_account(self, account_id: int, updates: AccountUpdateRequest) -> Dict[str, Any]:
        """Update an account"""
        try:
            success = await self.account_repo.update_account(account_id, updates)
            
            if not success:
                raise NotFoundError(f"Account with ID {account_id} not found")
            
            # Get updated account
            account = await self.account_repo.get_account_by_id(account_id)
            
            return {
                "success": True,
                "account": account
            }
            
        except Exception as e:
            raise e
    
    async def delete_account(self, account_id: int) -> Dict[str, Any]:
        """Delete an account"""
        try:
            success = await self.account_repo.delete_account(account_id)
            
            if not success:
                raise NotFoundError(f"Account with ID {account_id} not found")
            
            return {
                "success": True,
                "message": f"Account {account_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def search_accounts(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Search accounts by name or institution"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            accounts = await self.account_repo.search_accounts(query.strip(), user_id)
            
            return {
                "success": True,
                "accounts": accounts,
                "total_count": len(accounts)
            }
            
        except Exception as e:
            raise e
    
    # Security Management
    async def create_security(self, security_data: SecurityCreateRequest) -> Dict[str, Any]:
        """Create a new security"""
        try:
            security_id = await self.security_repo.create_security(security_data)
            
            # Get created security
            security = await self.security_repo.get_security_by_id(security_id)
            
            return {
                "success": True,
                "security_id": security_id,
                "security": security
            }
            
        except Exception as e:
            raise e
    
    async def get_security_by_id(self, security_id: int) -> Dict[str, Any]:
        """Get a single security by ID"""
        try:
            security = await self.security_repo.get_security_by_id(security_id)
            
            if not security:
                raise NotFoundError(f"Security with ID {security_id} not found")
            
            return {
                "success": True,
                "security": security
            }
            
        except Exception as e:
            raise e
    
    async def get_security_by_symbol(self, symbol: str, security_type: Optional[SecurityType] = None) -> Dict[str, Any]:
        """Get a single security by symbol"""
        try:
            security = await self.security_repo.get_security_by_symbol(symbol, security_type)
            
            if not security:
                raise NotFoundError(f"Security with symbol '{symbol}' not found")
            
            return {
                "success": True,
                "security": security
            }
            
        except Exception as e:
            raise e
    
    async def list_securities(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """List all securities with pagination"""
        try:
            securities = await self.security_repo.get_all_securities(limit, offset)
            
            return {
                "success": True,
                "securities": securities,
                "total_count": len(securities)
            }
            
        except Exception as e:
            raise e
    
    async def update_security(self, security_id: int, updates: SecurityUpdateRequest) -> Dict[str, Any]:
        """Update a security"""
        try:
            success = await self.security_repo.update_security(security_id, updates)
            
            if not success:
                raise NotFoundError(f"Security with ID {security_id} not found")
            
            # Get updated security
            security = await self.security_repo.get_security_by_id(security_id)
            
            return {
                "success": True,
                "security": security
            }
            
        except Exception as e:
            raise e
    
    async def delete_security(self, security_id: int) -> Dict[str, Any]:
        """Delete a security"""
        try:
            success = await self.security_repo.delete_security(security_id)
            
            if not success:
                raise NotFoundError(f"Security with ID {security_id} not found")
            
            return {
                "success": True,
                "message": f"Security {security_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def search_securities(self, query: str, security_type: Optional[SecurityType] = None) -> Dict[str, Any]:
        """Search securities by symbol or name"""
        try:
            if not query or len(query.strip()) < 1:
                raise ValidationError("Search query must be at least 1 character")
            
            securities = await self.security_repo.search_securities(query.strip(), security_type)
            
            return {
                "success": True,
                "securities": securities,
                "total_count": len(securities)
            }
            
        except Exception as e:
            raise e
    
    # Holding Management
    async def create_holding(self, holding_data: HoldingCreateRequest) -> Dict[str, Any]:
        """Create a new holding"""
        try:
            # Validate account exists
            account = await self.account_repo.get_account_by_id(holding_data.account_id)
            if not account:
                raise NotFoundError(f"Account with ID {holding_data.account_id} not found")
            
            # Validate security exists
            security = await self.security_repo.get_security_by_id(holding_data.security_id)
            if not security:
                raise NotFoundError(f"Security with ID {holding_data.security_id} not found")
            
            holding_id = await self.holding_repo.create_holding(holding_data)
            
            # Get created holding
            holding = await self.holding_repo.get_holding_by_id(holding_id)
            
            return {
                "success": True,
                "holding_id": holding_id,
                "holding": holding
            }
            
        except Exception as e:
            raise e
    
    async def get_holdings_by_account(self, account_id: int) -> Dict[str, Any]:
        """Get all holdings for an account"""
        try:
            holdings = await self.holding_repo.get_holdings_by_account(account_id)
            
            return {
                "success": True,
                "holdings": holdings,
                "total_count": len(holdings)
            }
            
        except Exception as e:
            raise e
    
    async def list_holdings(self, request: HoldingListRequest) -> Dict[str, Any]:
        """List holdings with optional filters"""
        try:
            holdings = await self.holding_repo.get_all_holdings(request)
            
            return {
                "success": True,
                "holdings": holdings,
                "total_count": len(holdings)
            }
            
        except Exception as e:
            raise e
    
    async def update_holding(self, holding_id: int, updates: HoldingUpdateRequest) -> Dict[str, Any]:
        """Update a holding"""
        try:
            success = await self.holding_repo.update_holding(holding_id, updates)
            
            if not success:
                raise NotFoundError(f"Holding with ID {holding_id} not found")
            
            # Get updated holding
            holding = await self.holding_repo.get_holding_by_id(holding_id)
            
            return {
                "success": True,
                "holding": holding
            }
            
        except Exception as e:
            raise e
    
    async def delete_holding(self, holding_id: int) -> Dict[str, Any]:
        """Delete a holding"""
        try:
            success = await self.holding_repo.delete_holding(holding_id)
            
            if not success:
                raise NotFoundError(f"Holding with ID {holding_id} not found")
            
            return {
                "success": True,
                "message": f"Holding {holding_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def get_portfolio_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get portfolio summary statistics"""
        try:
            summary = await self.holding_repo.get_portfolio_summary(user_id)
            
            return {
                "success": True,
                "portfolio_summary": summary
            }
            
        except Exception as e:
            raise e
    
    # Transaction Management
    async def create_transaction(self, transaction_data: TransactionCreateRequest) -> Dict[str, Any]:
        """Create a new transaction"""
        try:
            # Validate account exists
            account = await self.account_repo.get_account_by_id(transaction_data.account_id)
            if not account:
                raise NotFoundError(f"Account with ID {transaction_data.account_id} not found")
            
            # Validate security if provided
            if transaction_data.security_id:
                security = await self.security_repo.get_security_by_id(transaction_data.security_id)
                if not security:
                    raise NotFoundError(f"Security with ID {transaction_data.security_id} not found")
            
            transaction_id = await self.transaction_repo.create_transaction(transaction_data)
            
            # Get created transaction
            transaction = await self.transaction_repo.get_transaction_by_id(transaction_id)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "transaction": transaction
            }
            
        except Exception as e:
            raise e
    
    async def get_transaction_by_id(self, transaction_id: int) -> Dict[str, Any]:
        """Get a single transaction by ID"""
        try:
            transaction = await self.transaction_repo.get_transaction_by_id(transaction_id)
            
            if not transaction:
                raise NotFoundError(f"Transaction with ID {transaction_id} not found")
            
            return {
                "success": True,
                "transaction": transaction
            }
            
        except Exception as e:
            raise e
    
    async def get_transactions_by_account(self, account_id: int, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """Get all transactions for an account"""
        try:
            transactions = await self.transaction_repo.get_transactions_by_account(account_id, limit, offset)
            
            return {
                "success": True,
                "transactions": transactions,
                "total_count": len(transactions)
            }
            
        except Exception as e:
            raise e
    
    async def list_transactions(self, request: TransactionListRequest) -> Dict[str, Any]:
        """List transactions with optional filters"""
        try:
            transactions = await self.transaction_repo.get_all_transactions(request)
            
            return {
                "success": True,
                "transactions": transactions,
                "total_count": len(transactions)
            }
            
        except Exception as e:
            raise e
    
    async def update_transaction(self, transaction_id: int, updates: TransactionUpdateRequest) -> Dict[str, Any]:
        """Update a transaction"""
        try:
            success = await self.transaction_repo.update_transaction(transaction_id, updates)
            
            if not success:
                raise NotFoundError(f"Transaction with ID {transaction_id} not found")
            
            # Get updated transaction
            transaction = await self.transaction_repo.get_transaction_by_id(transaction_id)
            
            return {
                "success": True,
                "transaction": transaction
            }
            
        except Exception as e:
            raise e
    
    async def delete_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """Delete a transaction"""
        try:
            success = await self.transaction_repo.delete_transaction(transaction_id)
            
            if not success:
                raise NotFoundError(f"Transaction with ID {transaction_id} not found")
            
            return {
                "success": True,
                "message": f"Transaction {transaction_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def search_transactions(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Search transactions by description, category, or symbol"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            transactions = await self.transaction_repo.search_transactions(query.strip(), user_id)
            
            return {
                "success": True,
                "transactions": transactions,
                "total_count": len(transactions)
            }
            
        except Exception as e:
            raise e
    
    # File Import Management
    async def import_file(self, file_data: bytes, file_type: str, request: FileImportRequest) -> Dict[str, Any]:
        """Process uploaded file and import data"""
        try:
            result = await self.file_import_repo.process_file_upload(file_data, file_type, request)
            
            return {
                "success": True,
                "import_result": result
            }
            
        except Exception as e:
            raise e
    
    # Analytics
    async def get_portfolio_performance(self, user_id: Optional[str] = None, period_days: int = 365) -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        try:
            performance = await self.analytics_repo.get_portfolio_performance(user_id, period_days)
            
            return {
                "success": True,
                "performance": performance
            }
            
        except Exception as e:
            raise e
    
    async def get_account_performance(self, account_id: int, period_days: int = 365) -> Dict[str, Any]:
        """Get account performance metrics"""
        try:
            performance = await self.analytics_repo.get_account_performance(account_id, period_days)
            
            return {
                "success": True,
                "performance": performance
            }
            
        except Exception as e:
            raise e
    
    async def get_asset_allocation(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get asset allocation breakdown"""
        try:
            allocation = await self.analytics_repo.get_asset_allocation(user_id)
            
            return {
                "success": True,
                "asset_allocation": allocation
            }
            
        except Exception as e:
            raise e
    
    async def get_income_expense_analysis(self, user_id: Optional[str] = None, period_days: int = 365) -> Dict[str, Any]:
        """Get income and expense analysis"""
        try:
            analysis = await self.analytics_repo.get_income_expense_analysis(user_id, period_days)
            
            return {
                "success": True,
                "income_expense_analysis": analysis
            }
            
        except Exception as e:
            raise e


class PersonalFinanceIntegrationService:
    """Service for personal finance integration operations"""
    
    def __init__(self, integration_repo: PersonalFinanceIntegrationRepository):
        self.integration_repo = integration_repo
    
    async def sync_all_connections(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Sync all active connections for a user"""
        try:
            # This would typically get all connections for the user
            # and trigger sync for each one
            # For now, return a mock response
            
            return {
                "success": True,
                "sync_results": [
                    {
                        "connection_id": 1,
                        "status": "SUCCESS",
                        "records_processed": 100,
                        "duration_seconds": 45.2
                    }
                ],
                "total_connections": 1
            }
            
        except Exception as e:
            raise e
    
    async def get_sync_status(self, connection_id: int) -> Dict[str, Any]:
        """Get detailed connection status"""
        try:
            status = await self.integration_repo.get_connection_status(connection_id)
            
            return {
                "success": True,
                "connection_status": status
            }
            
        except Exception as e:
            raise e
    
    async def refresh_all_tokens(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Refresh authentication tokens for all connections"""
        try:
            # This would get all connections for the user
            # and refresh tokens for each one
            # For now, return a mock response
            
            return {
                "success": True,
                "refresh_results": [
                    {
                        "connection_id": 1,
                        "status": "SUCCESS",
                        "new_token_expires": datetime.utcnow() + timedelta(hours=1)
                    }
                ],
                "total_connections": 1
            }
            
        except Exception as e:
            raise e
