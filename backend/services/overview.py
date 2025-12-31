"""
Personal Finance Overview Service

Provides finance overview data for the Personal Finance Overview page.
Can pull from the database when connections exist, or falls back to mock data.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import os


class SourceType(str, Enum):
    AGGREGATOR = "AGGREGATOR"
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
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CRYPTO = "CRYPTO"
    UNKNOWN = "UNKNOWN"


def _get_overview_from_database() -> Optional[Dict[str, Any]]:
    """
    Attempt to get overview data from the finance database.
    Returns None if no connections exist or on error.
    """
    try:
        from services.finance import (
            get_all_connections, get_accounts_by_connection,
            get_account_total_value, get_institution_by_id
        )
        
        connections = get_all_connections()
        if not connections:
            return None
        
        custodians = []
        
        for conn in connections:
            if conn.status.value == "DISABLED":
                continue
            
            # Get institution
            institution = get_institution_by_id(conn.institution_id)
            if not institution:
                continue
            
            # Get accounts
            accounts = get_accounts_by_connection(conn.id)
            
            account_list = []
            total_value = 0.0
            
            for acct in accounts:
                acct_value = get_account_total_value(acct.id)
                total_value += acct_value
                
                account_list.append({
                    "accountId": str(acct.id),
                    "accountName": acct.name,
                    "accountType": acct.account_type.value,
                    "accountSubtype": acct.account_subtype.value if acct.account_subtype else "UNKNOWN",
                    "value": {
                        "value": acct_value,
                        "currency": acct.currency
                    }
                })
            
            custodian = {
                "institutionId": str(institution.id),
                "institutionName": institution.name,
                "sourceType": institution.source_type.value,
                "connection": {
                    "connectionId": str(conn.id),
                    "status": conn.status.value,
                    "lastSyncedAt": conn.last_synced_at,
                    "lastErrorMessage": conn.last_error_message
                },
                "totalValue": {
                    "value": total_value,
                    "currency": "USD"
                },
                "accounts": account_list
            }
            custodians.append(custodian)
        
        if not custodians:
            return None
        
        net_worth = sum(c["totalValue"]["value"] for c in custodians)
        
        return {
            "asOf": datetime.utcnow().isoformat() + "Z",
            "netWorthTotal": {
                "value": net_worth,
                "currency": "USD"
            },
            "custodians": custodians,
            "source": "database"
        }
        
    except Exception as e:
        print(f"Error loading from database: {e}")
        return None


# =============================================================================
# FALLBACK MOCK DATA - Used when no database connections exist
# =============================================================================

MOCK_INSTITUTIONS = {
    "inst_fidelity": {
        "id": "inst_fidelity",
        "name": "Fidelity",
        "brand_key": "fidelity",
        "source_type": SourceType.FILE_IMPORT,
        "logo_url": None
    },
    "inst_vanguard": {
        "id": "inst_vanguard",
        "name": "Vanguard",
        "brand_key": "vanguard",
        "source_type": SourceType.FILE_IMPORT,
        "logo_url": None
    },
    "inst_robinhood_crypto": {
        "id": "inst_robinhood_crypto",
        "name": "Robinhood (Crypto)",
        "brand_key": "robinhood",
        "source_type": SourceType.ROBINHOOD_CRYPTO,
        "logo_url": None
    },
    "inst_schwab": {
        "id": "inst_schwab",
        "name": "Charles Schwab",
        "brand_key": "schwab",
        "source_type": SourceType.AGGREGATOR,
        "logo_url": None
    }
}

MOCK_CONNECTIONS = {
    "conn_fidelity": {
        "id": "conn_fidelity",
        "institution_id": "inst_fidelity",
        "status": ConnectionStatus.ACTIVE,
        "last_synced_at": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
        "last_error_message": None
    },
    "conn_vanguard": {
        "id": "conn_vanguard",
        "institution_id": "inst_vanguard",
        "status": ConnectionStatus.ACTIVE,
        "last_synced_at": (datetime.utcnow() - timedelta(hours=4)).isoformat() + "Z",
        "last_error_message": None
    },
    "conn_robinhood": {
        "id": "conn_robinhood",
        "institution_id": "inst_robinhood_crypto",
        "status": ConnectionStatus.ACTIVE,
        "last_synced_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        "last_error_message": None
    }
}

MOCK_ACCOUNTS = {
    "acct_fidelity_roth": {
        "id": "acct_fidelity_roth",
        "connection_id": "conn_fidelity",
        "name": "Roth IRA",
        "account_type": AccountType.RETIREMENT,
        "account_subtype": AccountSubtype.ROTH_IRA,
        "currency": "USD",
        "is_closed": False,
        "value": 42500.00
    },
    "acct_fidelity_brokerage": {
        "id": "acct_fidelity_brokerage",
        "connection_id": "conn_fidelity",
        "name": "Individual Brokerage",
        "account_type": AccountType.BROKERAGE,
        "account_subtype": AccountSubtype.TAXABLE,
        "currency": "USD",
        "is_closed": False,
        "value": 28750.50
    },
    "acct_vanguard_401k": {
        "id": "acct_vanguard_401k",
        "connection_id": "conn_vanguard",
        "name": "401(k)",
        "account_type": AccountType.RETIREMENT,
        "account_subtype": AccountSubtype.K401,
        "currency": "USD",
        "is_closed": False,
        "value": 85000.00
    },
    "acct_robinhood_crypto": {
        "id": "acct_robinhood_crypto",
        "connection_id": "conn_robinhood",
        "name": "Crypto Wallet",
        "account_type": AccountType.CRYPTO,
        "account_subtype": AccountSubtype.CRYPTO,
        "currency": "USD",
        "is_closed": False,
        "value": 2340.75
    }
}


def get_accounts_for_connection(connection_id: str) -> List[Dict[str, Any]]:
    """Get all accounts for a given connection (mock data)."""
    return [
        {
            "accountId": acct["id"],
            "accountName": acct["name"],
            "accountType": acct["account_type"].value if isinstance(acct["account_type"], AccountType) else acct["account_type"],
            "accountSubtype": acct["account_subtype"].value if isinstance(acct["account_subtype"], AccountSubtype) else acct["account_subtype"],
            "value": {
                "value": acct["value"],
                "currency": acct["currency"]
            }
        }
        for acct in MOCK_ACCOUNTS.values()
        if acct["connection_id"] == connection_id and not acct["is_closed"]
    ]


def get_connection_total(connection_id: str) -> float:
    """Get total value for all accounts in a connection (mock data)."""
    return sum(
        acct["value"]
        for acct in MOCK_ACCOUNTS.values()
        if acct["connection_id"] == connection_id and not acct["is_closed"]
    )


def _get_mock_overview() -> Dict[str, Any]:
    """Get overview using fallback mock data."""
    custodians = []
    
    for conn_id, conn in MOCK_CONNECTIONS.items():
        inst = MOCK_INSTITUTIONS.get(conn["institution_id"])
        if not inst:
            continue
            
        if conn["status"] == ConnectionStatus.DISABLED:
            continue
            
        accounts = get_accounts_for_connection(conn_id)
        total_value = get_connection_total(conn_id)
        
        custodian = {
            "institutionId": inst["id"],
            "institutionName": inst["name"],
            "sourceType": inst["source_type"].value if isinstance(inst["source_type"], SourceType) else inst["source_type"],
            "connection": {
                "connectionId": conn["id"],
                "status": conn["status"].value if isinstance(conn["status"], ConnectionStatus) else conn["status"],
                "lastSyncedAt": conn["last_synced_at"],
                "lastErrorMessage": conn["last_error_message"]
            },
            "totalValue": {
                "value": total_value,
                "currency": "USD"
            },
            "accounts": accounts
        }
        custodians.append(custodian)
    
    net_worth = sum(c["totalValue"]["value"] for c in custodians)
    
    return {
        "asOf": datetime.utcnow().isoformat() + "Z",
        "netWorthTotal": {
            "value": net_worth,
            "currency": "USD"
        },
        "custodians": custodians,
        "source": "mock"
    }


def get_finance_overview() -> Dict[str, Any]:
    """
    Get the complete personal finance overview.
    Tries database first, falls back to mock data if no connections exist.
    """
    # Try database first
    db_result = _get_overview_from_database()
    if db_result:
        return db_result
    
    # Fall back to mock data
    return _get_mock_overview()


def get_connections_list() -> List[Dict[str, Any]]:
    """Get list of all connections for the Connections page."""
    # Try from database first
    try:
        from services.finance import get_all_connections, get_institution_by_id
        
        connections = get_all_connections()
        if connections:
            result = []
            for conn in connections:
                institution = get_institution_by_id(conn.institution_id)
                if not institution:
                    continue
                
                result.append({
                    "connectionId": str(conn.id),
                    "institutionId": str(institution.id),
                    "institutionName": institution.name,
                    "sourceType": institution.source_type.value,
                    "status": conn.status.value,
                    "lastSyncedAt": conn.last_synced_at,
                    "lastErrorMessage": conn.last_error_message
                })
            
            if result:
                return result
    except Exception as e:
        print(f"Error getting connections from database: {e}")
    
    # Fall back to mock data
    connections_list = []
    
    for conn_id, conn in MOCK_CONNECTIONS.items():
        inst = MOCK_INSTITUTIONS.get(conn["institution_id"])
        if not inst:
            continue
            
        connections_list.append({
            "connectionId": conn["id"],
            "institutionId": inst["id"],
            "institutionName": inst["name"],
            "sourceType": inst["source_type"].value if isinstance(inst["source_type"], SourceType) else inst["source_type"],
            "status": conn["status"].value if isinstance(conn["status"], ConnectionStatus) else conn["status"],
            "lastSyncedAt": conn["last_synced_at"],
            "lastErrorMessage": conn["last_error_message"]
        })
    
    return connections_list


def trigger_sync(connection_id: str) -> Dict[str, Any]:
    """
    Trigger a sync for a connection.
    Uses the connector framework if available.
    """
    try:
        from services.finance import sync_connection, SyncMode
        
        # Try to parse as int for database ID
        try:
            conn_id_int = int(connection_id)
            result = sync_connection(conn_id_int, SyncMode.INCREMENTAL, "USER")
            return result
        except ValueError:
            pass
    except Exception as e:
        print(f"Error triggering sync via connector: {e}")
    
    # Mock fallback
    if connection_id not in MOCK_CONNECTIONS and not connection_id.isdigit():
        return {"success": False, "error": "Connection not found"}
    
    return {
        "success": True,
        "message": "Sync started",
        "connectionId": connection_id
    }
