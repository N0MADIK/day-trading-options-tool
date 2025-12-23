"""
Personal Finance Overview Service

Provides mock data for the Personal Finance Overview page.
This will be replaced with real database queries and connector integrations.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum


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


# =============================================================================
# MOCK DATA - Replace with database queries in production
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
        "status": ConnectionStatus.NEEDS_REAUTH,
        "last_synced_at": (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
        "last_error_message": "Session expired. Please re-upload a recent statement."
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
    """Get all accounts for a given connection."""
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
    """Get total value for all accounts in a connection."""
    return sum(
        acct["value"]
        for acct in MOCK_ACCOUNTS.values()
        if acct["connection_id"] == connection_id and not acct["is_closed"]
    )


def get_finance_overview() -> Dict[str, Any]:
    """
    Get the complete personal finance overview.
    Returns data in the format expected by the frontend.
    """
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
    
    # Calculate net worth
    net_worth = sum(c["totalValue"]["value"] for c in custodians)
    
    return {
        "asOf": datetime.utcnow().isoformat() + "Z",
        "netWorthTotal": {
            "value": net_worth,
            "currency": "USD"
        },
        "custodians": custodians
    }


def get_connections_list() -> List[Dict[str, Any]]:
    """Get list of all connections for the Connections page."""
    connections = []
    
    for conn_id, conn in MOCK_CONNECTIONS.items():
        inst = MOCK_INSTITUTIONS.get(conn["institution_id"])
        if not inst:
            continue
            
        connections.append({
            "connectionId": conn["id"],
            "institutionId": inst["id"],
            "institutionName": inst["name"],
            "sourceType": inst["source_type"].value if isinstance(inst["source_type"], SourceType) else inst["source_type"],
            "status": conn["status"].value if isinstance(conn["status"], ConnectionStatus) else conn["status"],
            "lastSyncedAt": conn["last_synced_at"],
            "lastErrorMessage": conn["last_error_message"]
        })
    
    return connections


def trigger_sync(connection_id: str) -> Dict[str, Any]:
    """
    Trigger a sync for a connection.
    In production, this would queue a background job.
    For now, just return success with updated timestamp.
    """
    if connection_id not in MOCK_CONNECTIONS:
        return {"success": False, "error": "Connection not found"}
    
    # In production: queue sync job
    # For mock: just return success
    return {
        "success": True,
        "message": "Sync started",
        "connectionId": connection_id
    }
