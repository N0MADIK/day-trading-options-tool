from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional
import json

from app.services.personal_finance_service import PersonalFinanceService, PersonalFinanceIntegrationService
from app.repositories.sqlalchemy.personal_finance_repo import (
    SQLAlchemyInstitutionRepository, SQLAlchemyConnectionRepository,
    SQLAlchemyAccountRepository, SQLAlchemySecurityRepository,
    SQLAlchemyHoldingRepository, SQLAlchemyTransactionRepository,
    SQLAlchemySyncJobRepository, SQLAlchemyFileImportRepository,
    SQLAlchemyPersonalFinanceAnalyticsRepository,
    SQLAlchemyPersonalFinanceIntegrationRepository
)
from app.infrastructure.db import get_async_session
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

# Create routers for different personal finance modules
router = APIRouter(prefix="/personal-finance", tags=["personal-finance"])

institutions_router = APIRouter(prefix="/institutions", tags=["institutions"])
connections_router = APIRouter(prefix="/connections", tags=["connections"])
accounts_router = APIRouter(prefix="/accounts", tags=["accounts"])
securities_router = APIRouter(prefix="/securities", tags=["securities"])
holdings_router = APIRouter(prefix="/holdings", tags=["holdings"])
transactions_router = APIRouter(prefix="/transactions", tags=["transactions"])
sync_router = APIRouter(prefix="/sync", tags=["sync"])
import_router = APIRouter(prefix="/import", tags=["file-import"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])

# Dependencies for services
async def get_personal_finance_service() -> PersonalFinanceService:
    """Get personal finance service with repository"""
    session = await get_async_session()
    institution_repo = SQLAlchemyInstitutionRepository(session)
    connection_repo = SQLAlchemyConnectionRepository(session)
    account_repo = SQLAlchemyAccountRepository(session)
    security_repo = SQLAlchemySecurityRepository(session)
    holding_repo = SQLAlchemyHoldingRepository(session)
    transaction_repo = SQLAlchemyTransactionRepository(session)
    sync_job_repo = SQLAlchemySyncJobRepository(session)
    file_import_repo = SQLAlchemyFileImportRepository(session)
    analytics_repo = SQLAlchemyPersonalFinanceAnalyticsRepository(session)
    integration_repo = SQLAlchemyPersonalFinanceIntegrationRepository(session)
    return PersonalFinanceService(
        institution_repo, connection_repo, account_repo, security_repo, holding_repo,
        transaction_repo, sync_job_repo, file_import_repo, analytics_repo, integration_repo
    )

async def get_integration_service() -> PersonalFinanceIntegrationService:
    """Get integration service with repository"""
    session = await get_async_session()
    integration_repo = SQLAlchemyPersonalFinanceIntegrationRepository(session)
    return PersonalFinanceIntegrationService(integration_repo)

# Institution Endpoints
@institutions_router.post("/", response_model=dict)
async def create_institution(
    institution_data: InstitutionCreateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Create a new institution"""
    try:
        return await service.create_institution(institution_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@institutions_router.get("/", response_model=dict)
async def list_institutions(
    source_type: Optional[SourceType] = Query(None, description="Filter by source type"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """List institutions with optional filters"""
    try:
        request = InstitutionListRequest(
            source_type=source_type,
            limit=limit,
            offset=offset
        )
        return await service.list_institutions(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@institutions_router.get("/{institution_id}", response_model=dict)
async def get_institution_by_id(
    institution_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single institution by ID"""
    try:
        return await service.get_institution_by_id(institution_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@institutions_router.put("/{institution_id}", response_model=dict)
async def update_institution(
    institution_id: int,
    updates: InstitutionUpdateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Update an institution"""
    try:
        return await service.update_institution(institution_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@institutions_router.delete("/{institution_id}", response_model=dict)
async def delete_institution(
    institution_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Delete an institution"""
    try:
        return await service.delete_institution(institution_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@institutions_router.get("/search", response_model=dict)
async def search_institutions(
    q: str = Query(..., min_length=2, description="Search query"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Search institutions by name or brand key"""
    try:
        return await service.search_institutions(q)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Connection Endpoints
@connections_router.post("/", response_model=dict)
async def create_connection(
    connection_data: ConnectionCreateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Create a new connection"""
    try:
        return await service.create_connection(connection_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.get("/", response_model=dict)
async def list_connections(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    institution_id: Optional[int] = Query(None, description="Filter by institution ID"),
    source_type: Optional[SourceType] = Query(None, description="Filter by source type"),
    status: Optional[ConnectionStatus] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """List connections with optional filters"""
    try:
        request = ConnectionListRequest(
            user_id=user_id,
            institution_id=institution_id,
            source_type=source_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return await service.list_connections(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.get("/{connection_id}", response_model=dict)
async def get_connection_by_id(
    connection_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single connection by ID"""
    try:
        return await service.get_connection_by_id(connection_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.put("/{connection_id}", response_model=dict)
async def update_connection(
    connection_id: int,
    updates: ConnectionUpdateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Update a connection"""
    try:
        return await service.update_connection(connection_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.delete("/{connection_id}", response_model=dict)
async def delete_connection(
    connection_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Delete a connection"""
    try:
        return await service.delete_connection(connection_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.post("/{connection_id}/test", response_model=dict)
async def test_connection(
    connection_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Test connection connectivity and authentication"""
    try:
        return await service.test_connection(connection_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.post("/{connection_id}/sync", response_model=dict)
async def trigger_sync(
    connection_id: int,
    sync_mode: SyncMode = Query(SyncMode.INCREMENTAL, description="Sync mode"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Trigger manual sync for a connection"""
    try:
        return await service.trigger_sync(connection_id, sync_mode)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@connections_router.get("/needing-reauth", response_model=dict)
async def get_connections_needing_reauth(
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get connections that need re-authentication"""
    try:
        return await service.get_connections_needing_reauth()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Account Endpoints
@accounts_router.post("/", response_model=dict)
async def create_account(
    account_data: AccountCreateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Create a new account"""
    try:
        return await service.create_account(account_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@accounts_router.get("/", response_model=dict)
async def list_accounts(
    connection_id: Optional[int] = Query(None, description="Filter by connection ID"),
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    account_subtype: Optional[AccountSubtype] = Query(None, description="Filter by account subtype"),
    is_closed: Optional[bool] = Query(None, description="Filter by closed status"),
    currency: Optional[str] = Query(None, max_length=3, description="Filter by currency"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """List accounts with optional filters"""
    try:
        request = AccountListRequest(
            connection_id=connection_id,
            account_type=account_type,
            account_subtype=account_subtype,
            is_closed=is_closed,
            currency=currency,
            limit=limit,
            offset=offset
        )
        return await service.list_accounts(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@accounts_router.get("/{account_id}", response_model=dict)
async def get_account_by_id(
    account_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single account by ID"""
    try:
        return await service.get_account_by_id(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@accounts_router.put("/{account_id}", response_model=dict)
async def update_account(
    account_id: int,
    updates: AccountUpdateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Update an account"""
    try:
        return await service.update_account(account_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@accounts_router.delete("/{account_id}", response_model=dict)
async def delete_account(
    account_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Delete an account"""
    try:
        return await service.delete_account(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@accounts_router.get("/search", response_model=dict)
async def search_accounts(
    q: str = Query(..., min_length=2, description="Search query"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Search accounts by name or institution"""
    try:
        return await service.search_accounts(q, user_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Security Endpoints
@securities_router.post("/", response_model=dict)
async def create_security(
    security_data: SecurityCreateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Create a new security"""
    try:
        return await service.create_security(security_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.get("/", response_model=dict)
async def list_securities(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """List all securities with pagination"""
    try:
        return await service.list_securities(limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.get("/{security_id}", response_model=dict)
async def get_security_by_id(
    security_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single security by ID"""
    try:
        return await service.get_security_by_id(security_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.get("/symbol/{symbol}", response_model=dict)
async def get_security_by_symbol(
    symbol: str,
    security_type: Optional[SecurityType] = Query(None, description="Filter by security type"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single security by symbol"""
    try:
        return await service.get_security_by_symbol(symbol, security_type)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.put("/{security_id}", response_model=dict)
async def update_security(
    security_id: int,
    updates: SecurityUpdateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Update a security"""
    try:
        return await service.update_security(security_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.delete("/{security_id}", response_model=dict)
async def delete_security(
    security_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Delete a security"""
    try:
        return await service.delete_security(security_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.get("/search", response_model=dict)
async def search_securities(
    q: str = Query(..., min_length=1, description="Search query"),
    security_type: Optional[SecurityType] = Query(None, description="Filter by security type"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Search securities by symbol or name"""
    try:
        return await service.search_securities(q, security_type)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@securities_router.get("/popular", response_model=dict)
async def get_popular_securities(
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get most frequently traded securities"""
    try:
        securities = await service.security_repo.get_popular_securities(limit)
        
        return {
            "success": True,
            "securities": securities,
            "total_count": len(securities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Holding Endpoints
@holdings_router.post("/", response_model=dict)
async def create_holding(
    holding_data: HoldingCreateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Create a new holding"""
    try:
        return await service.create_holding(holding_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@holdings_router.get("/account/{account_id}", response_model=dict)
async def get_holdings_by_account(
    account_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get all holdings for an account"""
    try:
        return await service.get_holdings_by_account(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@holdings_router.get("/", response_model=dict)
async def list_holdings(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    security_id: Optional[int] = Query(None, description="Filter by security ID"),
    currency: Optional[str] = Query(None, max_length=3, description="Filter by currency"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """List holdings with optional filters"""
    try:
        request = HoldingListRequest(
            account_id=account_id,
            security_id=security_id,
            currency=currency,
            limit=limit,
            offset=offset
        )
        return await service.list_holdings(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@holdings_router.get("/{holding_id}", response_model=dict)
async def get_holding_by_id(
    holding_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single holding by ID"""
    try:
        holding = await service.holding_repo.get_holding_by_id(holding_id)
        if not holding:
            raise HTTPException(status_code=404, detail="Holding not found")
        
        return {
            "success": True,
            "holding": holding
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@holdings_router.put("/{holding_id}", response_model=dict)
async def update_holding(
    holding_id: int,
    updates: HoldingUpdateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Update a holding"""
    try:
        return await service.update_holding(holding_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@holdings_router.delete("/{holding_id}", response_model=dict)
async def delete_holding(
    holding_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Delete a holding"""
    try:
        return await service.delete_holding(holding_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@holdings_router.get("/portfolio-summary", response_model=dict)
async def get_portfolio_summary(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get portfolio summary statistics"""
    try:
        return await service.get_portfolio_summary(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Transaction Endpoints
@transactions_router.post("/", response_model=dict)
async def create_transaction(
    transaction_data: TransactionCreateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Create a new transaction"""
    try:
        return await service.create_transaction(transaction_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactions_router.get("/", response_model=dict)
async def list_transactions(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    security_id: Optional[int] = Query(None, description="Filter by security ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    category: Optional[str] = Query(None, max_length=100, description="Filter by category"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """List transactions with optional filters"""
    try:
        request = TransactionListRequest(
            account_id=account_id,
            security_id=security_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=limit,
            offset=offset
        )
        return await service.list_transactions(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactions_router.get("/{transaction_id}", response_model=dict)
async def get_transaction_by_id(
    transaction_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get a single transaction by ID"""
    try:
        return await service.get_transaction_by_id(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactions_router.get("/account/{account_id}", response_model=dict)
async def get_transactions_by_account(
    account_id: int,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get all transactions for an account"""
    try:
        return await service.get_transactions_by_account(account_id, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactions_router.put("/{transaction_id}", response_model=dict)
async def update_transaction(
    transaction_id: int,
    updates: TransactionUpdateRequest,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Update a transaction"""
    try:
        return await service.update_transaction(transaction_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactions_router.delete("/{transaction_id}", response_model=dict)
async def delete_transaction(
    transaction_id: int,
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Delete a transaction"""
    try:
        return await service.delete_transaction(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@transactions_router.get("/search", response_model=dict)
async def search_transactions(
    q: str = Query(..., min_length=2, description="Search query"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Search transactions by description, category, or symbol"""
    try:
        return await service.search_transactions(q, user_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File Import Endpoints
@import_router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(..., description="File to import"),
    file_type: str = Query(..., regex="^(csv|ofx|qfx)$", description="File type"),
    account_id: Optional[int] = Query(None, description="Target account ID"),
    connection_id: Optional[int] = Query(None, description="Target connection ID"),
    mapping: Optional[str] = Query(None, description="Field mapping configuration"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Process uploaded file and import data"""
    try:
        file_data = await file.read()
        
        mapping_dict = None
        if mapping:
            mapping_dict = json.loads(mapping)
        
        request = FileImportRequest(
            file_type=file_type,
            account_id=account_id,
            connection_id=connection_id,
            mapping=mapping_dict
        )
        
        return await service.import_file(file_data, file_type, request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@analytics_router.get("/portfolio-performance", response_model=dict)
async def get_portfolio_performance(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    period_days: int = Query(365, ge=1, le=3650, description="Period in days"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get portfolio performance metrics"""
    try:
        return await service.get_portfolio_performance(user_id, period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/account-performance/{account_id}", response_model=dict)
async def get_account_performance(
    account_id: int,
    period_days: int = Query(365, ge=1, le=3650, description="Period in days"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get account performance metrics"""
    try:
        return await service.get_account_performance(account_id, period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/asset-allocation", response_model=dict)
async def get_asset_allocation(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get asset allocation breakdown"""
    try:
        return await service.get_asset_allocation(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/income-expense-analysis", response_model=dict)
async def get_income_expense_analysis(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    period_days: int = Query(365, ge=1, le=3650, description="Period in days"),
    service: PersonalFinanceService = Depends(get_personal_finance_service)
):
    """Get income and expense analysis"""
    try:
        return await service.get_income_expense_analysis(user_id, period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Integration Endpoints
@router.post("/sync-all", response_model=dict)
async def sync_all_connections(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    service: PersonalFinanceIntegrationService = Depends(get_integration_service)
):
    """Sync all active connections for a user"""
    try:
        return await service.sync_all_connections(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh-all-tokens", response_model=dict)
async def refresh_all_tokens(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    service: PersonalFinanceIntegrationService = Depends(get_integration_service)
):
    """Refresh authentication tokens for all connections"""
    try:
        return await service.refresh_all_tokens(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync-status/{connection_id}", response_model=dict)
async def get_sync_status(
    connection_id: int,
    service: PersonalFinanceIntegrationService = Depends(get_integration_service)
):
    """Get detailed connection status"""
    try:
        return await service.get_sync_status(connection_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include sub-routers
router.include_router(institutions_router)
router.include_router(connections_router)
router.include_router(accounts_router)
router.include_router(securities_router)
router.include_router(holdings_router)
router.include_router(transactions_router)
router.include_router(import_router)
router.include_router(analytics_router)
