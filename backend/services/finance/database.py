"""
Finance Database Layer

SQLite database operations for personal finance entities.
"""
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import (
    Institution, Connection, Account, Security, Holding, Transaction, 
    RawEvent, SyncJob, SourceType, ConnectionStatus, AccountType, 
    AccountSubtype, SecurityType, TransactionType, SyncMode, SyncStatus
)

# Database path
FINANCE_DB_PATH = Path(__file__).parent.parent.parent / "data" / "finance.db"


def get_finance_db():
    """Get database connection with row factory."""
    FINANCE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FINANCE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_finance_db():
    """Initialize finance database schema."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    # Institutions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS institutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand_key TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL,
            logo_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Connections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            institution_id INTEGER NOT NULL,
            source_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            auth_blob_encrypted TEXT,
            last_synced_at TEXT,
            next_sync_at TEXT,
            last_error_code TEXT,
            last_error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        )
    """)
    
    # Accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_id INTEGER NOT NULL,
            external_account_id TEXT NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            account_subtype TEXT,
            currency TEXT DEFAULT 'USD',
            institution_masked_number TEXT,
            is_closed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connection_id) REFERENCES connections(id),
            UNIQUE(connection_id, external_account_id)
        )
    """)
    
    # Securities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS securities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT,
            cusip TEXT,
            isin TEXT,
            security_type TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, security_type)
        )
    """)
    
    # Holdings table (current positions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            security_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            cost_basis_total REAL,
            cost_basis_per_unit REAL,
            price REAL,
            value REAL,
            as_of TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES finance_accounts(id),
            FOREIGN KEY (security_id) REFERENCES securities(id),
            UNIQUE(account_id, security_id, as_of)
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            security_id INTEGER,
            external_txn_id TEXT,
            dedupe_key TEXT,
            transaction_type TEXT NOT NULL,
            trade_date TEXT,
            settle_date TEXT,
            posted_at TEXT NOT NULL,
            quantity REAL,
            price REAL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            description TEXT,
            raw_category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES finance_accounts(id),
            FOREIGN KEY (security_id) REFERENCES securities(id),
            UNIQUE(account_id, external_txn_id),
            UNIQUE(account_id, dedupe_key)
        )
    """)
    
    # Raw events table (for debugging/replay)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_id INTEGER NOT NULL,
            source_type TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            checksum TEXT NOT NULL,
            received_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connection_id) REFERENCES connections(id)
        )
    """)
    
    # Sync jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_id INTEGER NOT NULL,
            triggered_by TEXT NOT NULL DEFAULT 'USER',
            mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            started_at TEXT,
            finished_at TEXT,
            accounts_count INTEGER DEFAULT 0,
            holdings_count INTEGER DEFAULT 0,
            transactions_count INTEGER DEFAULT 0,
            error_summary TEXT,
            attempt_count INTEGER DEFAULT 1,
            FOREIGN KEY (connection_id) REFERENCES connections(id)
        )
    """)
    
    # Insert default institutions
    default_institutions = [
        ("Fidelity", "fidelity", SourceType.FILE_IMPORT.value),
        ("Vanguard", "vanguard", SourceType.FILE_IMPORT.value),
        ("Charles Schwab", "schwab", SourceType.AGGREGATOR.value),
        ("Robinhood (Crypto)", "robinhood_crypto", SourceType.ROBINHOOD_CRYPTO.value),
        ("Plaid Connection", "plaid", SourceType.AGGREGATOR.value),
    ]
    
    for name, brand_key, source_type in default_institutions:
        cursor.execute("""
            INSERT OR IGNORE INTO institutions (name, brand_key, source_type)
            VALUES (?, ?, ?)
        """, (name, brand_key, source_type))
    
    conn.commit()
    conn.close()
    print("Finance database initialized")


# ============================================================================
# INSTITUTION OPERATIONS
# ============================================================================

def get_all_institutions() -> List[Institution]:
    """Get all institutions."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM institutions ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    return [Institution(
        id=row["id"],
        name=row["name"],
        brand_key=row["brand_key"],
        source_type=SourceType(row["source_type"]),
        logo_url=row["logo_url"],
        created_at=row["created_at"]
    ) for row in rows]


def get_institution_by_id(institution_id: int) -> Optional[Institution]:
    """Get institution by ID."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM institutions WHERE id = ?", (institution_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return Institution(
        id=row["id"],
        name=row["name"],
        brand_key=row["brand_key"],
        source_type=SourceType(row["source_type"]),
        logo_url=row["logo_url"],
        created_at=row["created_at"]
    )


def get_institution_by_brand_key(brand_key: str) -> Optional[Institution]:
    """Get institution by brand key."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM institutions WHERE brand_key = ?", (brand_key,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return Institution(
        id=row["id"],
        name=row["name"],
        brand_key=row["brand_key"],
        source_type=SourceType(row["source_type"]),
        logo_url=row["logo_url"],
        created_at=row["created_at"]
    )


# ============================================================================
# CONNECTION OPERATIONS
# ============================================================================

def create_connection(
    institution_id: int,
    source_type: SourceType,
    auth_blob_encrypted: Optional[str] = None,
    user_id: str = "default"
) -> int:
    """Create a new connection."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO connections 
        (user_id, institution_id, source_type, status, auth_blob_encrypted, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, institution_id, source_type.value, ConnectionStatus.ACTIVE.value, 
          auth_blob_encrypted, now, now))
    
    connection_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return connection_id


def get_all_connections(user_id: str = "default") -> List[Connection]:
    """Get all connections for a user."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM connections WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [Connection(
        id=row["id"],
        user_id=row["user_id"],
        institution_id=row["institution_id"],
        source_type=SourceType(row["source_type"]),
        status=ConnectionStatus(row["status"]),
        auth_blob_encrypted=row["auth_blob_encrypted"],
        last_synced_at=row["last_synced_at"],
        next_sync_at=row["next_sync_at"],
        last_error_code=row["last_error_code"],
        last_error_message=row["last_error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    ) for row in rows]


def get_connection_by_id(connection_id: int) -> Optional[Connection]:
    """Get connection by ID."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return Connection(
        id=row["id"],
        user_id=row["user_id"],
        institution_id=row["institution_id"],
        source_type=SourceType(row["source_type"]),
        status=ConnectionStatus(row["status"]),
        auth_blob_encrypted=row["auth_blob_encrypted"],
        last_synced_at=row["last_synced_at"],
        next_sync_at=row["next_sync_at"],
        last_error_code=row["last_error_code"],
        last_error_message=row["last_error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


def update_connection_status(
    connection_id: int, 
    status: ConnectionStatus,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Update connection status."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        UPDATE connections 
        SET status = ?, last_error_code = ?, last_error_message = ?, updated_at = ?
        WHERE id = ?
    """, (status.value, error_code, error_message, now, connection_id))
    
    conn.commit()
    conn.close()


def update_connection_sync_time(connection_id: int):
    """Update last synced timestamp."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        UPDATE connections 
        SET last_synced_at = ?, updated_at = ?
        WHERE id = ?
    """, (now, now, connection_id))
    
    conn.commit()
    conn.close()


def update_connection_auth(connection_id: int, auth_blob_encrypted: str):
    """Update connection auth blob."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        UPDATE connections 
        SET auth_blob_encrypted = ?, status = ?, updated_at = ?
        WHERE id = ?
    """, (auth_blob_encrypted, ConnectionStatus.ACTIVE.value, now, connection_id))
    
    conn.commit()
    conn.close()


# ============================================================================
# ACCOUNT OPERATIONS
# ============================================================================

def upsert_account(
    connection_id: int,
    external_account_id: str,
    name: str,
    account_type: AccountType,
    account_subtype: AccountSubtype = AccountSubtype.UNKNOWN,
    currency: str = "USD",
    masked_number: Optional[str] = None
) -> int:
    """Insert or update an account."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO finance_accounts 
        (connection_id, external_account_id, name, account_type, account_subtype, 
         currency, institution_masked_number, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(connection_id, external_account_id) DO UPDATE SET
            name = excluded.name,
            account_type = excluded.account_type,
            account_subtype = excluded.account_subtype,
            currency = excluded.currency,
            institution_masked_number = excluded.institution_masked_number,
            updated_at = excluded.updated_at
    """, (connection_id, external_account_id, name, account_type.value, 
          account_subtype.value, currency, masked_number, now, now))
    
    # Get the ID (either inserted or existing)
    cursor.execute("""
        SELECT id FROM finance_accounts 
        WHERE connection_id = ? AND external_account_id = ?
    """, (connection_id, external_account_id))
    account_id = cursor.fetchone()["id"]
    
    conn.commit()
    conn.close()
    
    return account_id


def get_accounts_by_connection(connection_id: int) -> List[Account]:
    """Get all accounts for a connection."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM finance_accounts 
        WHERE connection_id = ? AND is_closed = 0
        ORDER BY name
    """, (connection_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [Account(
        id=row["id"],
        connection_id=row["connection_id"],
        external_account_id=row["external_account_id"],
        name=row["name"],
        account_type=AccountType(row["account_type"]),
        account_subtype=AccountSubtype(row["account_subtype"]) if row["account_subtype"] else AccountSubtype.UNKNOWN,
        currency=row["currency"],
        institution_masked_number=row["institution_masked_number"],
        is_closed=bool(row["is_closed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    ) for row in rows]


def get_account_by_id(account_id: int) -> Optional[Account]:
    """Get account by ID."""
    conn = get_finance_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM finance_accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return Account(
        id=row["id"],
        connection_id=row["connection_id"],
        external_account_id=row["external_account_id"],
        name=row["name"],
        account_type=AccountType(row["account_type"]),
        account_subtype=AccountSubtype(row["account_subtype"]) if row["account_subtype"] else AccountSubtype.UNKNOWN,
        currency=row["currency"],
        institution_masked_number=row["institution_masked_number"],
        is_closed=bool(row["is_closed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


# ============================================================================
# SECURITY OPERATIONS
# ============================================================================

def upsert_security(
    symbol: str,
    security_type: SecurityType,
    name: Optional[str] = None,
    cusip: Optional[str] = None,
    isin: Optional[str] = None
) -> int:
    """Insert or update a security."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO securities (symbol, name, cusip, isin, security_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, security_type) DO UPDATE SET
            name = COALESCE(excluded.name, securities.name),
            cusip = COALESCE(excluded.cusip, securities.cusip),
            isin = COALESCE(excluded.isin, securities.isin)
    """, (symbol, name, cusip, isin, security_type.value, now))
    
    # Get the ID
    cursor.execute("""
        SELECT id FROM securities WHERE symbol = ? AND security_type = ?
    """, (symbol, security_type.value))
    security_id = cursor.fetchone()["id"]
    
    conn.commit()
    conn.close()
    
    return security_id


def get_security_by_symbol(symbol: str, security_type: Optional[SecurityType] = None) -> Optional[Security]:
    """Get security by symbol."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    if security_type:
        cursor.execute("""
            SELECT * FROM securities WHERE symbol = ? AND security_type = ?
        """, (symbol, security_type.value))
    else:
        cursor.execute("SELECT * FROM securities WHERE symbol = ?", (symbol,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return Security(
        id=row["id"],
        symbol=row["symbol"],
        name=row["name"],
        cusip=row["cusip"],
        isin=row["isin"],
        security_type=SecurityType(row["security_type"]),
        created_at=row["created_at"]
    )


# ============================================================================
# HOLDING OPERATIONS
# ============================================================================

def upsert_holding(
    account_id: int,
    security_id: int,
    quantity: float,
    as_of: str,
    cost_basis_total: Optional[float] = None,
    cost_basis_per_unit: Optional[float] = None,
    price: Optional[float] = None,
    value: Optional[float] = None
) -> int:
    """Insert or update a holding."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO holdings 
        (account_id, security_id, quantity, cost_basis_total, cost_basis_per_unit,
         price, value, as_of, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_id, security_id, as_of) DO UPDATE SET
            quantity = excluded.quantity,
            cost_basis_total = excluded.cost_basis_total,
            cost_basis_per_unit = excluded.cost_basis_per_unit,
            price = excluded.price,
            value = excluded.value
    """, (account_id, security_id, quantity, cost_basis_total, cost_basis_per_unit,
          price, value, as_of, now))
    
    holding_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return holding_id


def get_holdings_by_account(account_id: int, as_of: Optional[str] = None) -> List[Holding]:
    """Get holdings for an account."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    if as_of:
        cursor.execute("""
            SELECT * FROM holdings WHERE account_id = ? AND as_of = ?
        """, (account_id, as_of))
    else:
        # Get latest holdings per security
        cursor.execute("""
            SELECT h.* FROM holdings h
            INNER JOIN (
                SELECT account_id, security_id, MAX(as_of) as max_as_of
                FROM holdings WHERE account_id = ?
                GROUP BY account_id, security_id
            ) latest ON h.account_id = latest.account_id 
                AND h.security_id = latest.security_id 
                AND h.as_of = latest.max_as_of
        """, (account_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [Holding(
        id=row["id"],
        account_id=row["account_id"],
        security_id=row["security_id"],
        quantity=row["quantity"],
        cost_basis_total=row["cost_basis_total"],
        cost_basis_per_unit=row["cost_basis_per_unit"],
        price=row["price"],
        value=row["value"],
        as_of=row["as_of"],
        created_at=row["created_at"]
    ) for row in rows]


def get_account_total_value(account_id: int) -> float:
    """Get total value of holdings in an account."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    # Get latest holdings
    cursor.execute("""
        SELECT COALESCE(SUM(h.value), 0) as total FROM holdings h
        INNER JOIN (
            SELECT account_id, security_id, MAX(as_of) as max_as_of
            FROM holdings WHERE account_id = ?
            GROUP BY account_id, security_id
        ) latest ON h.account_id = latest.account_id 
            AND h.security_id = latest.security_id 
            AND h.as_of = latest.max_as_of
    """, (account_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result["total"] if result else 0.0


# ============================================================================
# TRANSACTION OPERATIONS
# ============================================================================

def generate_dedupe_key(account_id: int, posted_at: str, amount: float, 
                        description: str, security_id: Optional[int] = None) -> str:
    """Generate a deterministic dedupe key for transactions without external IDs."""
    data = f"{account_id}|{posted_at}|{amount}|{description}|{security_id or ''}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def upsert_transaction(
    account_id: int,
    transaction_type: TransactionType,
    posted_at: str,
    amount: float,
    description: str,
    security_id: Optional[int] = None,
    external_txn_id: Optional[str] = None,
    trade_date: Optional[str] = None,
    settle_date: Optional[str] = None,
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    currency: str = "USD",
    raw_category: Optional[str] = None
) -> int:
    """Insert or update a transaction."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    # Generate dedupe key if no external ID
    dedupe_key = None
    if not external_txn_id:
        dedupe_key = generate_dedupe_key(account_id, posted_at, amount, description, security_id)
    
    try:
        cursor.execute("""
            INSERT INTO finance_transactions 
            (account_id, security_id, external_txn_id, dedupe_key, transaction_type,
             trade_date, settle_date, posted_at, quantity, price, amount, currency,
             description, raw_category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (account_id, security_id, external_txn_id, dedupe_key, transaction_type.value,
              trade_date, settle_date, posted_at, quantity, price, amount, currency,
              description, raw_category, now))
        
        txn_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Already exists, get the existing ID
        if external_txn_id:
            cursor.execute("""
                SELECT id FROM finance_transactions 
                WHERE account_id = ? AND external_txn_id = ?
            """, (account_id, external_txn_id))
        else:
            cursor.execute("""
                SELECT id FROM finance_transactions 
                WHERE account_id = ? AND dedupe_key = ?
            """, (account_id, dedupe_key))
        
        txn_id = cursor.fetchone()["id"]
    
    conn.commit()
    conn.close()
    
    return txn_id


def get_transactions_by_account(
    account_id: int, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> List[Transaction]:
    """Get transactions for an account."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM finance_transactions WHERE account_id = ?"
    params = [account_id]
    
    if start_date:
        query += " AND posted_at >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND posted_at <= ?"
        params.append(end_date)
    
    query += " ORDER BY posted_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [Transaction(
        id=row["id"],
        account_id=row["account_id"],
        security_id=row["security_id"],
        external_txn_id=row["external_txn_id"],
        dedupe_key=row["dedupe_key"],
        transaction_type=TransactionType(row["transaction_type"]),
        trade_date=row["trade_date"],
        settle_date=row["settle_date"],
        posted_at=row["posted_at"],
        quantity=row["quantity"],
        price=row["price"],
        amount=row["amount"],
        currency=row["currency"],
        description=row["description"],
        raw_category=row["raw_category"],
        created_at=row["created_at"]
    ) for row in rows]


# ============================================================================
# RAW EVENT OPERATIONS
# ============================================================================

def record_raw_event(
    connection_id: int,
    source_type: SourceType,
    event_type: str,
    payload: Dict[str, Any]
) -> int:
    """Record a raw event for debugging/replay."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    payload_json = json.dumps(payload, default=str)
    checksum = hashlib.sha256(payload_json.encode()).hexdigest()
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO raw_events (connection_id, source_type, event_type, payload_json, checksum, received_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (connection_id, source_type.value, event_type, payload_json, checksum, now))
    
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return event_id


# ============================================================================
# SYNC JOB OPERATIONS
# ============================================================================

def create_sync_job(connection_id: int, mode: SyncMode, triggered_by: str = "USER") -> int:
    """Create a sync job record."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO sync_jobs (connection_id, triggered_by, mode, status, started_at)
        VALUES (?, ?, ?, ?, ?)
    """, (connection_id, triggered_by, mode.value, SyncStatus.RUNNING.value, now))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return job_id


def update_sync_job(
    job_id: int,
    status: SyncStatus,
    accounts_count: int = 0,
    holdings_count: int = 0,
    transactions_count: int = 0,
    error_summary: Optional[str] = None
):
    """Update sync job status and metrics."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        UPDATE sync_jobs SET
            status = ?, finished_at = ?,
            accounts_count = ?, holdings_count = ?, transactions_count = ?,
            error_summary = ?
        WHERE id = ?
    """, (status.value, now, accounts_count, holdings_count, transactions_count, 
          error_summary, job_id))
    
    conn.commit()
    conn.close()


def get_sync_jobs_by_connection(connection_id: int, limit: int = 10) -> List[SyncJob]:
    """Get recent sync jobs for a connection."""
    conn = get_finance_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sync_jobs WHERE connection_id = ?
        ORDER BY started_at DESC LIMIT ?
    """, (connection_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [SyncJob(
        id=row["id"],
        connection_id=row["connection_id"],
        triggered_by=row["triggered_by"],
        mode=SyncMode(row["mode"]),
        status=SyncStatus(row["status"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        accounts_count=row["accounts_count"],
        holdings_count=row["holdings_count"],
        transactions_count=row["transactions_count"],
        error_summary=row["error_summary"],
        attempt_count=row["attempt_count"]
    ) for row in rows]
