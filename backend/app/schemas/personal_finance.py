from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Data source type enumeration"""
    AGGREGATOR = "AGGREGATOR"
    SNAPTRADE = "SNAPTRADE"
    ROBINHOOD_CRYPTO = "ROBINHOOD_CRYPTO"
    FILE_IMPORT = "FILE_IMPORT"


class ConnectionStatus(str, Enum):
    """Connection status enumeration"""
    ACTIVE = "ACTIVE"
    NEEDS_REAUTH = "NEEDS_REAUTH"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


class AccountType(str, Enum):
    """Account type enumeration"""
    BROKERAGE = "BROKERAGE"
    RETIREMENT = "RETIREMENT"
    CASH = "CASH"
    CRYPTO = "CRYPTO"
    UNKNOWN = "UNKNOWN"


class AccountSubtype(str, Enum):
    """Account subtype enumeration"""
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
    """Security type enumeration"""
    EQUITY = "EQUITY"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    BOND = "BOND"
    CRYPTO = "CRYPTO"
    CASH = "CASH"
    OPTION = "OPTION"
    UNKNOWN = "UNKNOWN"


class TransactionType(str, Enum):
    """Transaction type enumeration"""
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
    """Sync mode enumeration"""
    INITIAL = "INITIAL"
    INCREMENTAL = "INCREMENTAL"


class SyncStatus(str, Enum):
    """Sync status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# Institution Models
class InstitutionCreateRequest(BaseModel):
    """Request for creating an institution"""
    name: str = Field(..., min_length=1, max_length=200, description="Institution name")
    brand_key: str = Field(..., min_length=1, max_length=100, description="Unique brand identifier")
    source_type: SourceType = Field(..., description="Source type")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip()
    
    @validator('brand_key')
    def normalize_brand_key(cls, v):
        return v.strip().upper()


class InstitutionUpdateRequest(BaseModel):
    """Request for updating an institution"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Institution name")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")


class InstitutionResponse(BaseModel):
    """Response model for institution data"""
    id: int
    name: str
    brand_key: str
    source_type: SourceType
    logo_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Connection Models
class ConnectionCreateRequest(BaseModel):
    """Request for creating a connection"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    institution_id: int = Field(..., description="Institution ID")
    source_type: SourceType = Field(..., description="Source type")
    auth_data: Optional[Dict[str, Any]] = Field(None, description="Authentication data")
    status: Optional[ConnectionStatus] = Field(ConnectionStatus.ACTIVE, description="Connection status")


class ConnectionUpdateRequest(BaseModel):
    """Request for updating a connection"""
    status: Optional[ConnectionStatus] = Field(None, description="Connection status")
    auth_data: Optional[Dict[str, Any]] = Field(None, description="Updated authentication data")
    last_error_code: Optional[str] = Field(None, max_length=50, description="Last error code")
    last_error_message: Optional[str] = Field(None, max_length=500, description="Last error message")


class ConnectionResponse(BaseModel):
    """Response model for connection data"""
    id: int
    user_id: str
    institution_id: int
    source_type: SourceType
    status: ConnectionStatus
    last_synced_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConnectionWithInstitutionResponse(BaseModel):
    """Response model for connection with institution data"""
    id: int
    user_id: str
    institution: InstitutionResponse
    source_type: SourceType
    status: ConnectionStatus
    last_synced_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Account Models
class AccountCreateRequest(BaseModel):
    """Request for creating an account"""
    connection_id: int = Field(..., description="Connection ID")
    external_account_id: str = Field(..., min_length=1, max_length=100, description="External account ID")
    name: str = Field(..., min_length=1, max_length=200, description="Account name")
    account_type: AccountType = Field(..., description="Account type")
    account_subtype: Optional[AccountSubtype] = Field(None, description="Account subtype")
    currency: str = Field("USD", max_length=3, description="Currency code")
    institution_masked_number: Optional[str] = Field(None, max_length=50, description="Masked account number")
    is_closed: bool = Field(False, description="Whether account is closed")


class AccountUpdateRequest(BaseModel):
    """Request for updating an account"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Account name")
    account_subtype: Optional[AccountSubtype] = Field(None, description="Account subtype")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    institution_masked_number: Optional[str] = Field(None, max_length=50, description="Masked account number")
    is_closed: Optional[bool] = Field(None, description="Whether account is closed")


class AccountResponse(BaseModel):
    """Response model for account data"""
    id: int
    connection_id: int
    external_account_id: str
    name: str
    account_type: AccountType
    account_subtype: Optional[AccountSubtype] = None
    currency: str
    institution_masked_number: Optional[str] = None
    is_closed: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AccountWithConnectionResponse(BaseModel):
    """Response model for account with connection data"""
    id: int
    external_account_id: str
    name: str
    account_type: AccountType
    account_subtype: Optional[AccountSubtype] = None
    currency: str
    institution_masked_number: Optional[str] = None
    is_closed: bool
    connection: ConnectionWithInstitutionResponse
    total_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# Security Models
class SecurityCreateRequest(BaseModel):
    """Request for creating a security"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Security symbol")
    name: Optional[str] = Field(None, max_length=200, description="Security name")
    cusip: Optional[str] = Field(None, max_length=20, description="CUSIP identifier")
    isin: Optional[str] = Field(None, max_length=20, description="ISIN identifier")
    security_type: SecurityType = Field(..., description="Security type")
    
    @validator('symbol')
    def normalize_symbol(cls, v):
        return v.strip().upper()


class SecurityUpdateRequest(BaseModel):
    """Request for updating a security"""
    name: Optional[str] = Field(None, max_length=200, description="Security name")
    cusip: Optional[str] = Field(None, max_length=20, description="CUSIP identifier")
    isin: Optional[str] = Field(None, max_length=20, description="ISIN identifier")


class SecurityResponse(BaseModel):
    """Response model for security data"""
    id: int
    symbol: str
    name: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    security_type: SecurityType
    created_at: datetime
    
    class Config:
        from_attributes = True


# Holding Models
class HoldingCreateRequest(BaseModel):
    """Request for creating a holding"""
    account_id: int = Field(..., description="Account ID")
    security_id: int = Field(..., description="Security ID")
    quantity: float = Field(..., description="Number of shares/units")
    cost_basis: float = Field(..., description="Total cost basis")
    market_value: float = Field(..., description="Current market value")
    currency: str = Field("USD", max_length=3, description="Currency code")
    as_of_date: Optional[datetime] = Field(None, description="As of date for market value")


class HoldingUpdateRequest(BaseModel):
    """Request for updating a holding"""
    quantity: Optional[float] = Field(None, description="Number of shares/units")
    cost_basis: Optional[float] = Field(None, description="Total cost basis")
    market_value: Optional[float] = Field(None, description="Current market value")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    as_of_date: Optional[datetime] = Field(None, description="As of date for market value")


class HoldingResponse(BaseModel):
    """Response model for holding data"""
    id: int
    account_id: int
    security_id: int
    quantity: float
    cost_basis: float
    market_value: float
    currency: str
    as_of_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HoldingWithSecurityResponse(BaseModel):
    """Response model for holding with security data"""
    id: int
    account_id: int
    security: SecurityResponse
    quantity: float
    cost_basis: float
    market_value: float
    currency: str
    as_of_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Transaction Models
class TransactionCreateRequest(BaseModel):
    """Request for creating a transaction"""
    account_id: int = Field(..., description="Account ID")
    security_id: Optional[int] = Field(None, description="Security ID")
    external_transaction_id: Optional[str] = Field(None, max_length=100, description="External transaction ID")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    quantity: Optional[float] = Field(None, description="Number of shares/units")
    amount: Optional[float] = Field(None, description="Transaction amount")
    price: Optional[float] = Field(None, description="Price per share/unit")
    fees: Optional[float] = Field(None, description="Transaction fees")
    currency: str = Field("USD", max_length=3, description="Currency code")
    transaction_date: datetime = Field(..., description="Transaction date")
    settle_date: Optional[datetime] = Field(None, description="Settlement date")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    category: Optional[str] = Field(None, max_length=100, description="Transaction category")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw transaction data")


class TransactionUpdateRequest(BaseModel):
    """Request for updating a transaction"""
    security_id: Optional[int] = Field(None, description="Security ID")
    external_transaction_id: Optional[str] = Field(None, max_length=100, description="External transaction ID")
    transaction_type: Optional[TransactionType] = Field(None, description="Transaction type")
    quantity: Optional[float] = Field(None, description="Number of shares/units")
    amount: Optional[float] = Field(None, description="Transaction amount")
    price: Optional[float] = Field(None, description="Price per share/unit")
    fees: Optional[float] = Field(None, description="Transaction fees")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    settle_date: Optional[datetime] = Field(None, description="Settlement date")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    category: Optional[str] = Field(None, max_length=100, description="Transaction category")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw transaction data")


class TransactionResponse(BaseModel):
    """Response model for transaction data"""
    id: int
    account_id: int
    security_id: Optional[int] = None
    external_transaction_id: Optional[str] = None
    transaction_type: TransactionType
    quantity: Optional[float] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    fees: Optional[float] = None
    currency: str
    transaction_date: datetime
    settle_date: Optional[datetime] = None
    description: Optional[str] = None
    category: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionWithSecurityResponse(BaseModel):
    """Response model for transaction with security data"""
    id: int
    account_id: int
    security: Optional[SecurityResponse] = None
    external_transaction_id: Optional[str] = None
    transaction_type: TransactionType
    quantity: Optional[float] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    fees: Optional[float] = None
    currency: str
    transaction_date: datetime
    settle_date: Optional[datetime] = None
    description: Optional[str] = None
    category: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# Sync Job Models
class SyncJobCreateRequest(BaseModel):
    """Request for creating a sync job"""
    connection_id: int = Field(..., description="Connection ID")
    sync_mode: SyncMode = Field(..., description="Sync mode")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled execution time")


class SyncJobUpdateRequest(BaseModel):
    """Request for updating a sync job"""
    status: Optional[SyncStatus] = Field(None, description="Sync status")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    records_processed: Optional[int] = Field(None, description="Number of records processed")
    records_success: Optional[int] = Field(None, description="Number of successful records")
    records_failed: Optional[int] = Field(None, description="Number of failed records")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message")
    output: Optional[Dict[str, Any]] = Field(None, description="Sync output data")


class SyncJobResponse(BaseModel):
    """Response model for sync job data"""
    id: int
    connection_id: int
    sync_mode: SyncMode
    status: SyncStatus
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_processed: Optional[int] = None
    records_success: Optional[int] = None
    records_failed: Optional[int] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# File Import Models
class FileImportRequest(BaseModel):
    """Request for file import"""
    file_type: str = Field(..., regex="^(csv|ofx|qfx)$", description="File type (csv, ofx, qfx)")
    account_id: Optional[int] = Field(None, description="Target account ID")
    connection_id: Optional[int] = Field(None, description="Target connection ID")
    mapping: Optional[Dict[str, str]] = Field(None, description="Field mapping configuration")


class FileImportResponse(BaseModel):
    """Response model for file import results"""
    import_id: str
    status: str
    records_processed: int
    records_imported: int
    records_failed: int
    errors: List[str] = Field(default=[])
    created_accounts: List[AccountResponse] = Field(default=[])
    created_securities: List[SecurityResponse] = Field(default=[])
    imported_transactions: List[TransactionResponse] = Field(default=[])


# Analytics Models
class PortfolioSummaryResponse(BaseModel):
    """Response model for portfolio summary"""
    total_value: float = Field(..., description="Total portfolio value")
    total_cost_basis: float = Field(..., description="Total cost basis")
    total_gain_loss: float = Field(..., description="Total gain/loss")
    total_gain_loss_percentage: float = Field(..., description="Total gain/loss percentage")
    account_count: int = Field(..., description="Number of accounts")
    holding_count: int = Field(..., description="Number of holdings")
    security_count: int = Field(..., description="Number of unique securities")
    currency_breakdown: Dict[str, float] = Field(default={}, description="Value breakdown by currency")
    account_type_breakdown: Dict[str, float] = Field(default={}, description="Value breakdown by account type")


class AccountPerformanceResponse(BaseModel):
    """Response model for account performance"""
    account_id: int
    account_name: str
    total_value: float
    total_cost_basis: float
    gain_loss: float
    gain_loss_percentage: float
    transaction_count: int
    holding_count: int


class SecurityPerformanceResponse(BaseModel):
    """Response model for security performance"""
    security_id: int
    symbol: str
    name: Optional[str] = None
    total_quantity: float
    total_cost_basis: float
    total_market_value: float
    gain_loss: float
    gain_loss_percentage: float
    holding_accounts: List[int] = Field(default=[])
    transaction_count: int


# List and Filter Models
class InstitutionListRequest(BaseModel):
    """Request for listing institutions"""
    source_type: Optional[SourceType] = Field(None, description="Filter by source type")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class ConnectionListRequest(BaseModel):
    """Request for listing connections"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    institution_id: Optional[int] = Field(None, description="Filter by institution ID")
    source_type: Optional[SourceType] = Field(None, description="Filter by source type")
    status: Optional[ConnectionStatus] = Field(None, description="Filter by status")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class AccountListRequest(BaseModel):
    """Request for listing accounts"""
    connection_id: Optional[int] = Field(None, description="Filter by connection ID")
    account_type: Optional[AccountType] = Field(None, description="Filter by account type")
    account_subtype: Optional[AccountSubtype] = Field(None, description="Filter by account subtype")
    is_closed: Optional[bool] = Field(None, description="Filter by closed status")
    currency: Optional[str] = Field(None, max_length=3, description="Filter by currency")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class HoldingListRequest(BaseModel):
    """Request for listing holdings"""
    account_id: Optional[int] = Field(None, description="Filter by account ID")
    security_id: Optional[int] = Field(None, description="Filter by security ID")
    currency: Optional[str] = Field(None, max_length=3, description="Filter by currency")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class TransactionListRequest(BaseModel):
    """Request for listing transactions"""
    account_id: Optional[int] = Field(None, description="Filter by account ID")
    security_id: Optional[int] = Field(None, description="Filter by security ID")
    transaction_type: Optional[TransactionType] = Field(None, description="Filter by transaction type")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    category: Optional[str] = Field(None, max_length=100, description="Filter by category")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class SyncJobListRequest(BaseModel):
    """Request for listing sync jobs"""
    connection_id: Optional[int] = Field(None, description="Filter by connection ID")
    sync_mode: Optional[SyncMode] = Field(None, description="Filter by sync mode")
    status: Optional[SyncStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")
