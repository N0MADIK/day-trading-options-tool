import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.personal_finance_service import PersonalFinanceService, PersonalFinanceIntegrationService
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


class TestPersonalFinanceService:
    """Test personal finance service operations"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'institution_repo': AsyncMock(spec=SQLAlchemyInstitutionRepository),
            'connection_repo': AsyncMock(spec=SQLAlchemyConnectionRepository),
            'account_repo': AsyncMock(spec=SQLAlchemyAccountRepository),
            'security_repo': AsyncMock(spec=SQLAlchemySecurityRepository),
            'holding_repo': AsyncMock(spec=SQLAlchemyHoldingRepository),
            'transaction_repo': AsyncMock(spec=SQLAlchemyTransactionRepository),
            'sync_job_repo': AsyncMock(spec=SQLAlchemySyncJobRepository),
            'file_import_repo': AsyncMock(spec=SQLAlchemyFileImportRepository),
            'analytics_repo': AsyncMock(spec=SQLAlchemyPersonalFinanceAnalyticsRepository),
            'integration_repo': AsyncMock(spec=SQLAlchemyPersonalFinanceIntegrationRepository)
        }
    
    @pytest.fixture
    def personal_finance_service(self, mock_repositories):
        """Create personal finance service with mock repositories"""
        return PersonalFinanceService(
            mock_repositories['institution_repo'],
            mock_repositories['connection_repo'],
            mock_repositories['account_repo'],
            mock_repositories['security_repo'],
            mock_repositories['holding_repo'],
            mock_repositories['transaction_repo'],
            mock_repositories['sync_job_repo'],
            mock_repositories['file_import_repo'],
            mock_repositories['analytics_repo'],
            mock_repositories['integration_repo']
        )
    
    @pytest.mark.asyncio
    async def test_create_institution_success(self, personal_finance_service, mock_repositories):
        """Test successful institution creation"""
        # Setup
        institution_data = InstitutionCreateRequest(
            name="Test Bank",
            brand_key="TESTBANK",
            source_type=SourceType.AGGREGATOR,
            logo_url="https://example.com/logo.png"
        )
        mock_repositories['institution_repo'].get_institution_by_brand_key.return_value(None)
        mock_repositories['institution_repo'].create_institution.return_value(1)
        
        # Execute
        result = await personal_finance_service.create_institution(institution_data)
        
        # Assert
        assert result["success"] is True
        assert result["institution_id"] == 1
        assert "institution" in result
        mock_repositories['institution_repo'].get_institution_by_brand_key.assert_called_once_with("TESTBANK")
        mock_repositories['institution_repo'].create_institution.assert_called_once_with(institution_data)
    
    @pytest.mark.asyncio
    async def test_create_institution_duplicate_brand_key(self, personal_finance_service, mock_repositories):
        """Test institution creation with duplicate brand key"""
        # Setup
        institution_data = InstitutionCreateRequest(
            name="Test Bank",
            brand_key="TESTBANK",
            source_type=SourceType.AGGREGATOR
        )
        mock_repositories['institution_repo'].get_institution_by_brand_key.return_value(
            {"id": 1, "name": "Existing Bank"}
        )
        
        # Execute & Assert
        with pytest.raises(ConflictError) as exc_info:
            await personal_finance_service.create_institution(institution_data)
        assert "already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_institution_by_id_success(self, personal_finance_service, mock_repositories):
        """Test successful institution retrieval by ID"""
        # Setup
        mock_institution = {
            'id': 1,
            'name': 'Test Bank',
            'brand_key': 'TESTBANK',
            'source_type': SourceType.AGGREGATOR,
            'logo_url': 'https://example.com/logo.png',
            'created_at': datetime.utcnow()
        }
        mock_repositories['institution_repo'].get_institution_by_id.return_value(mock_institution)
        
        # Execute
        result = await personal_finance_service.get_institution_by_id(1)
        
        # Assert
        assert result["success"] is True
        assert result["institution"] == mock_institution
        mock_repositories['institution_repo'].get_institution_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_institution_by_id_not_found(self, personal_finance_service, mock_repositories):
        """Test institution retrieval when not found"""
        # Setup
        mock_repositories['institution_repo'].get_institution_by_id.return_value(None)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await personal_finance_service.get_institution_by_id(999)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_institutions_success(self, personal_finance_service, mock_repositories):
        """Test successful institution listing"""
        # Setup
        mock_institutions = [
            {
                'id': 1,
                'name': 'Bank A',
                'brand_key': 'BANKA',
                'source_type': SourceType.AGGREGATOR
            },
            {
                'id': 2,
                'name': 'Bank B',
                'brand_key': 'BANKB',
                'source_type': SourceType.SNAPTRADE
            }
        ]
        mock_repositories['institution_repo'].get_all_institutions.return_value(mock_institutions)
        
        # Execute
        result = await personal_finance_service.list_institutions(InstitutionListRequest())
        
        # Assert
        assert result["success"] is True
        assert len(result["institutions"]) == 2
        assert result["total_count"] == 2
    
    @pytest.mark.asyncio
    async def test_create_connection_success(self, personal_finance_service, mock_repositories):
        """Test successful connection creation"""
        # Setup
        connection_data = ConnectionCreateRequest(
            user_id="user123",
            institution_id=1,
            source_type=SourceType.SNAPTRADE,
            auth_data={"api_key": "test_key"},
            status=ConnectionStatus.ACTIVE
        )
        mock_repositories['institution_repo'].get_institution_by_id.return_value(
            {"id": 1, "name": "Test Bank"}
        )
        mock_repositories['connection_repo'].create_connection.return_value(1)
        mock_connection = {
            'id': 1,
            'user_id': 'user123',
            'institution_id': 1,
            'source_type': SourceType.SNAPTRADE,
            'status': ConnectionStatus.ACTIVE,
            'created_at': datetime.utcnow()
        }
        mock_repositories['connection_repo'].get_connection_by_id.return_value(mock_connection)
        
        # Execute
        result = await personal_finance_service.create_connection(connection_data)
        
        # Assert
        assert result["success"] is True
        assert result["connection_id"] == 1
        assert "connection" in result
        mock_repositories['institution_repo'].get_institution_by_id.assert_called_once_with(1)
        mock_repositories['connection_repo'].create_connection.assert_called_once_with(connection_data)
    
    @pytest.mark.asyncio
    async def test_create_connection_institution_not_found(self, personal_finance_service, mock_repositories):
        """Test connection creation when institution not found"""
        # Setup
        connection_data = ConnectionCreateRequest(
            user_id="user123",
            institution_id=999,
            source_type=SourceType.SNAPTRADE
        )
        mock_repositories['institution_repo'].get_institution_by_id.return_value(None)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await personal_finance_service.create_connection(connection_data)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, personal_finance_service, mock_repositories):
        """Test successful connection test"""
        # Setup
        mock_repositories['integration_repo'].test_connection.return_value({
            "success": True,
            "response_time_ms": 150,
            "last_tested": datetime.utcnow()
        })
        
        # Execute
        result = await personal_finance_service.test_connection(1)
        
        # Assert
        assert result["success"] is True
        assert "test_result" in result
        mock_repositories['integration_repo'].test_connection.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_trigger_sync_success(self, personal_finance_service, mock_repositories):
        """Test successful sync trigger"""
        # Setup
        mock_repositories['integration_repo'].trigger_manual_sync.return_value({
            "success": True,
            "sync_id": "sync_123",
            "estimated_duration_minutes": 5
        })
        mock_repositories['connection_repo'].update_connection_sync_time.return_value(True)
        
        # Execute
        result = await personal_finance_service.trigger_sync(1, SyncMode.INCREMENTAL)
        
        # Assert
        assert result["success"] is True
        assert "sync_result" in result
        mock_repositories['integration_repo'].trigger_manual_sync.assert_called_once_with(1, SyncMode.INCREMENTAL)
        mock_repositories['connection_repo'].update_connection_sync_time.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_account_success(self, personal_finance_service, mock_repositories):
        """Test successful account creation"""
        # Setup
        account_data = AccountCreateRequest(
            connection_id=1,
            external_account_id="ACC123456",
            name="Primary Checking",
            account_type=AccountType.CASH,
            account_subtype=AccountSubtype.CHECKING,
            currency="USD"
        )
        mock_repositories['account_repo'].create_account.return_value(1)
        mock_account = {
            'id': 1,
            'external_account_id': 'ACC123456',
            'name': 'Primary Checking',
            'account_type': AccountType.CASH,
            'currency': 'USD'
        }
        mock_repositories['account_repo'].get_account_by_id.return_value(mock_account)
        
        # Execute
        result = await personal_finance_service.create_account(account_data)
        
        # Assert
        assert result["success"] is True
        assert result["account_id"] == 1
        assert "account" in result
        mock_repositories['account_repo'].create_account.assert_called_once_with(account_data)
    
    @pytest.mark.asyncio
    async def test_get_portfolio_summary_success(self, personal_finance_service, mock_repositories):
        """Test successful portfolio summary retrieval"""
        # Setup
        mock_summary = {
            "total_value": 100000.0,
            "total_cost_basis": 80000.0,
            "total_gain_loss": 20000.0,
            "total_gain_loss_percentage": 25.0,
            "account_count": 5,
            "holding_count": 15,
            "security_count": 10,
            "currency_breakdown": {"USD": 100000.0},
            "account_type_breakdown": {"CASH": 20000.0, "BROKERAGE": 80000.0}
        }
        mock_repositories['holding_repo'].get_portfolio_summary.return_value(mock_summary)
        
        # Execute
        result = await personal_finance_service.get_portfolio_summary()
        
        # Assert
        assert result["success"] is True
        assert result["portfolio_summary"] == mock_summary
        mock_repositories['holding_repo'].get_portfolio_summary.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_security_success(self, personal_finance_service, mock_repositories):
        """Test successful security creation"""
        # Setup
        security_data = SecurityCreateRequest(
            symbol="AAPL",
            name="Apple Inc.",
            security_type=SecurityType.EQUITY,
            cusip="037833100"
        )
        mock_repositories['security_repo'].create_security.return_value(1)
        mock_security = {
            'id': 1,
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'security_type': SecurityType.EQUITY,
            'cusip': '037833100'
        }
        mock_repositories['security_repo'].get_security_by_id.return_value(mock_security)
        
        # Execute
        result = await personal_finance_service.create_security(security_data)
        
        # Assert
        assert result["success"] is True
        assert result["security_id"] == 1
        assert "security" in result
        mock_repositories['security_repo'].create_security.assert_called_once_with(security_data)
    
    @pytest.mark.asyncio
    async def test_get_security_by_symbol_success(self, personal_finance_service, mock_repositories):
        """Test successful security retrieval by symbol"""
        # Setup
        mock_security = {
            'id': 1,
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'security_type': SecurityType.EQUITY
        }
        mock_repositories['security_repo'].get_security_by_symbol.return_value(mock_security)
        
        # Execute
        result = await personal_finance_service.get_security_by_symbol("AAPL")
        
        # Assert
        assert result["success"] is True
        assert result["security"] == mock_security
        mock_repositories['security_repo'].get_security_by_symbol.assert_called_once_with("AAPL", None)
    
    @pytest.mark.asyncio
    async def test_create_transaction_success(self, personal_finance_service, mock_repositories):
        """Test successful transaction creation"""
        # Setup
        transaction_data = TransactionCreateRequest(
            account_id=1,
            security_id=1,
            transaction_type=TransactionType.BUY,
            quantity=100,
            amount=15000.0,
            price=150.0,
            transaction_date=datetime.utcnow()
        )
        mock_repositories['account_repo'].get_account_by_id.return_value({"id": 1})
        mock_repositories['security_repo'].get_security_by_id.return_value({"id": 1})
        mock_repositories['transaction_repo'].create_transaction.return_value(1)
        mock_transaction = {
            'id': 1,
            'account_id': 1,
            'security_id': 1,
            'transaction_type': TransactionType.BUY,
            'quantity': 100,
            'amount': 15000.0,
            'price': 150.0,
            'transaction_date': datetime.utcnow()
        }
        mock_repositories['transaction_repo'].get_transaction_by_id.return_value(mock_transaction)
        
        # Execute
        result = await personal_finance_service.create_transaction(transaction_data)
        
        # Assert
        assert result["success"] is True
        assert result["transaction_id"] == 1
        assert "transaction" in result
        mock_repositories['transaction_repo'].create_transaction.assert_called_once_with(transaction_data)
    
    @pytest.mark.asyncio
    async def test_search_institutions_success(self, personal_finance_service, mock_repositories):
        """Test successful institution search"""
        # Setup
        mock_institutions = [
            {
                'id': 1,
                'name': 'Test Bank',
                'brand_key': 'TESTBANK',
                'source_type': SourceType.AGGREGATOR
            }
        ]
        mock_repositories['institution_repo'].search_institutions.return_value(mock_institutions)
        
        # Execute
        result = await personal_finance_service.search_institutions("Test")
        
        # Assert
        assert result["success"] is True
        assert len(result["institutions"]) == 1
        assert result["total_count"] == 1
        mock_repositories['institution_repo'].search_institutions.assert_called_once_with("Test")
    
    @pytest.mark.asyncio
    async def test_search_institutions_invalid_query(self, personal_finance_service, mock_repositories):
        """Test institution search with invalid query"""
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await personal_finance_service.search_institutions("A")
        assert "at least 2 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_import_file_success(self, personal_finance_service, mock_repositories):
        """Test successful file import"""
        # Setup
        file_data = b"symbol,date,type,amount\nAAPL,2023-01-01,BUY,100"
        import_result = {
            "import_id": "import_123",
            "status": "success",
            "records_processed": 1,
            "records_imported": 1,
            "records_failed": 0,
            "errors": [],
            "created_accounts": [],
            "created_securities": [],
            "imported_transactions": []
        }
        mock_repositories['file_import_repo'].process_file_upload.return_value(import_result)
        
        # Execute
        request = FileImportRequest(
            file_type="csv",
            account_id=1
        )
        result = await personal_finance_service.import_file(file_data, "csv", request)
        
        # Assert
        assert result["success"] is True
        assert "import_result" in result
        mock_repositories['file_import_repo'].process_file_upload.assert_called_once()


class TestPersonalFinanceIntegrationService:
    """Test personal finance integration service operations"""
    
    @pytest.fixture
    def mock_integration_repo(self):
        """Create mock integration repository"""
        return AsyncMock(spec=SQLAlchemyPersonalFinanceIntegrationRepository)
    
    @pytest.fixture
    def integration_service(self, mock_integration_repo):
        """Create integration service with mock repository"""
        return PersonalFinanceIntegrationService(mock_integration_repo)
    
    @pytest.mark.asyncio
    async def test_sync_all_connections_success(self, integration_service, mock_integration_repo):
        """Test successful sync all connections"""
        # Setup
        sync_results = [
            {
                "connection_id": 1,
                "status": "SUCCESS",
                "records_processed": 100,
                "duration_seconds": 45.2
            }
        ]
        mock_integration_repo.sync_all_connections.return_value({
            "success": True,
            "sync_results": sync_results,
            "total_connections": 1
        })
        
        # Execute
        result = await integration_service.sync_all_connections()
        
        # Assert
        assert result["success"] is True
        assert len(result["sync_results"]) == 1
        assert result["total_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_refresh_all_tokens_success(self, integration_service, mock_integration_repo):
        """Test successful token refresh"""
        # Setup
        refresh_results = [
            {
                "connection_id": 1,
                "status": "SUCCESS",
                "new_token_expires": datetime.utcnow() + timedelta(hours=1)
            }
        ]
        mock_integration_repo.refresh_all_tokens.return_value({
            "success": True,
            "refresh_results": refresh_results,
            "total_connections": 1
        })
        
        # Execute
        result = await integration_service.refresh_all_tokens()
        
        # Assert
        assert result["success"] is True
        assert len(result["refresh_results"]) == 1
        assert result["total_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_get_sync_status_success(self, integration_service, mock_integration_repo):
        """Test successful sync status retrieval"""
        # Setup
        status_data = {
            "connection_id": 1,
            "status": "ACTIVE",
            "last_sync": datetime.utcnow(),
            "next_sync": datetime.utcnow() + timedelta(hours=24),
            "error_count": 0,
            "last_error": None
        }
        mock_integration_repo.get_connection_status.return_value(status_data)
        
        # Execute
        result = await integration_service.get_sync_status(1)
        
        # Assert
        assert result["success"] is True
        assert "connection_status" in result
        mock_integration_repo.get_connection_status.assert_called_once_with(1)
