"""
CSV Parser

Parser for CSV transaction exports from various brokerages.
Supports institution-specific field mappings.
"""
import csv
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from .models import AccountType, AccountSubtype, SecurityType, TransactionType
from .connectors import SyncResult, AccountDTO, HoldingDTO, TransactionDTO


# ============================================================================
# INSTITUTION-SPECIFIC MAPPINGS
# ============================================================================

# Each mapping defines how to extract data from that institution's CSV format
CSV_MAPPINGS = {
    "fidelity": {
        "name": "Fidelity",
        "delimiter": ",",
        "skip_rows": 0,  # Number of header rows to skip
        "encoding": "utf-8",
        "columns": {
            "date": ["Run Date", "Date", "Trade Date"],
            "action": ["Action", "Transaction Type"],
            "symbol": ["Symbol"],
            "description": ["Description", "Security Description"],
            "quantity": ["Quantity", "Shares"],
            "price": ["Price ($)", "Price"],
            "amount": ["Amount ($)", "Amount"],
            "settlement_date": ["Settlement Date"]
        },
        "date_formats": ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"],
        "action_mapping": {
            "YOU BOUGHT": TransactionType.BUY,
            "BOUGHT": TransactionType.BUY,
            "BUY": TransactionType.BUY,
            "YOU SOLD": TransactionType.SELL,
            "SOLD": TransactionType.SELL,
            "SELL": TransactionType.SELL,
            "DIVIDEND": TransactionType.DIVIDEND,
            "DIV": TransactionType.DIVIDEND,
            "INTEREST": TransactionType.INTEREST,
            "INT": TransactionType.INTEREST,
            "TRANSFER": TransactionType.TRANSFER_IN,
            "CONTRIBUTION": TransactionType.DEPOSIT,
            "DEPOSIT": TransactionType.DEPOSIT,
            "WITHDRAWAL": TransactionType.WITHDRAWAL,
        }
    },
    "vanguard": {
        "name": "Vanguard",
        "delimiter": ",",
        "skip_rows": 0,
        "encoding": "utf-8",
        "columns": {
            "date": ["Trade Date", "Settlement Date", "Date"],
            "action": ["Transaction Type", "Transaction Description"],
            "symbol": ["Symbol", "Ticker Symbol"],
            "description": ["Investment Name", "Fund Name", "Description"],
            "quantity": ["Shares", "Quantity"],
            "price": ["Share Price", "Price"],
            "amount": ["Dollar Amount", "Amount", "Principal Amount"]
        },
        "date_formats": ["%m/%d/%Y", "%Y-%m-%d"],
        "action_mapping": {
            "Buy": TransactionType.BUY,
            "Sell": TransactionType.SELL,
            "Dividend": TransactionType.DIVIDEND,
            "Capital gain": TransactionType.DIVIDEND,
            "Reinvestment": TransactionType.BUY,
            "Exchange": TransactionType.TRANSFER_IN,
            "Contribution": TransactionType.DEPOSIT,
            "Withdrawal": TransactionType.WITHDRAWAL,
        }
    },
    "schwab": {
        "name": "Charles Schwab",
        "delimiter": ",",
        "skip_rows": 0,
        "encoding": "utf-8",
        "columns": {
            "date": ["Date"],
            "action": ["Action"],
            "symbol": ["Symbol"],
            "description": ["Description"],
            "quantity": ["Quantity"],
            "price": ["Price"],
            "amount": ["Amount"],
            "fees": ["Fees & Comm"]
        },
        "date_formats": ["%m/%d/%Y"],
        "action_mapping": {
            "Buy": TransactionType.BUY,
            "Sell": TransactionType.SELL,
            "Qualified Dividend": TransactionType.DIVIDEND,
            "Cash Dividend": TransactionType.DIVIDEND,
            "Reinvest Dividend": TransactionType.BUY,
            "Stock Split": TransactionType.SPLIT,
            "Journal": TransactionType.TRANSFER_IN,
            "Wire Sent": TransactionType.WITHDRAWAL,
            "Wire Received": TransactionType.DEPOSIT,
        }
    },
    "generic": {
        "name": "Generic",
        "delimiter": ",",
        "skip_rows": 0,
        "encoding": "utf-8",
        "columns": {
            "date": ["Date", "Trade Date", "Transaction Date", "Posted Date"],
            "action": ["Type", "Action", "Transaction Type", "Description"],
            "symbol": ["Symbol", "Ticker", "Security"],
            "description": ["Description", "Memo", "Name"],
            "quantity": ["Quantity", "Shares", "Units", "Qty"],
            "price": ["Price", "Unit Price", "Share Price"],
            "amount": ["Amount", "Total", "Value", "Dollar Amount"]
        },
        "date_formats": ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y"],
        "action_mapping": {
            "BUY": TransactionType.BUY,
            "SELL": TransactionType.SELL,
            "DIVIDEND": TransactionType.DIVIDEND,
            "DIV": TransactionType.DIVIDEND,
            "INTEREST": TransactionType.INTEREST,
            "INT": TransactionType.INTEREST,
            "TRANSFER": TransactionType.TRANSFER_IN,
            "DEPOSIT": TransactionType.DEPOSIT,
            "WITHDRAWAL": TransactionType.WITHDRAWAL,
        }
    }
}


def find_column(headers: List[str], aliases: List[str]) -> Optional[int]:
    """Find the index of a column by trying multiple aliases."""
    headers_lower = [h.lower().strip() for h in headers]
    
    for alias in aliases:
        alias_lower = alias.lower().strip()
        if alias_lower in headers_lower:
            return headers_lower.index(alias_lower)
    
    return None


def parse_date(date_str: str, formats: List[str]) -> Optional[str]:
    """Try multiple date formats to parse a date string."""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat() + "Z"
        except:
            continue
    
    return None


def parse_number(value_str: str) -> Optional[float]:
    """Parse a number from a string, handling currency symbols and commas."""
    if not value_str:
        return None
    
    # Remove currency symbols, commas, and whitespace
    clean = re.sub(r'[$,\s]', '', value_str.strip())
    
    # Handle parentheses for negative numbers
    if clean.startswith('(') and clean.endswith(')'):
        clean = '-' + clean[1:-1]
    
    try:
        return float(clean)
    except:
        return None


def map_action_to_type(action: str, mapping: Dict[str, TransactionType]) -> TransactionType:
    """Map an action string to a TransactionType."""
    if not action:
        return TransactionType.UNKNOWN
    
    action_upper = action.upper().strip()
    
    # Try exact match first
    for key, txn_type in mapping.items():
        if key.upper() == action_upper:
            return txn_type
    
    # Try partial match
    for key, txn_type in mapping.items():
        if key.upper() in action_upper or action_upper in key.upper():
            return txn_type
    
    return TransactionType.UNKNOWN


def detect_delimiter(content: str) -> str:
    """Try to detect the CSV delimiter."""
    first_line = content.split('\n')[0]
    
    # Count potential delimiters
    delimiters = [',', '\t', ';', '|']
    counts = {d: first_line.count(d) for d in delimiters}
    
    # Return the one with highest count
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ','


def parse_csv_file(file_path: str, institution: str = "generic") -> SyncResult:
    """
    Parse a CSV file and extract transactions.
    
    Args:
        file_path: Path to the CSV file
        institution: Institution name for field mapping (fidelity, vanguard, schwab, generic)
        
    Returns:
        SyncResult with parsed transactions
    """
    try:
        # Get mapping for institution
        mapping = CSV_MAPPINGS.get(institution.lower(), CSV_MAPPINGS["generic"])
        
        # Read file
        with open(file_path, 'r', encoding=mapping.get("encoding", "utf-8"), errors="ignore") as f:
            content = f.read()
        
        # Detect delimiter if not specified
        delimiter = mapping.get("delimiter") or detect_delimiter(content)
        
        # Parse CSV
        lines = content.strip().split('\n')
        
        # Skip header rows if specified
        skip_rows = mapping.get("skip_rows", 0)
        lines = lines[skip_rows:]
        
        if not lines:
            return SyncResult(success=False, errors=["Empty CSV file"])
        
        reader = csv.reader(lines, delimiter=delimiter)
        rows = list(reader)
        
        if len(rows) < 2:
            return SyncResult(success=False, errors=["CSV file has no data rows"])
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Find column indices
        col_mapping = mapping.get("columns", {})
        date_idx = find_column(headers, col_mapping.get("date", []))
        action_idx = find_column(headers, col_mapping.get("action", []))
        symbol_idx = find_column(headers, col_mapping.get("symbol", []))
        desc_idx = find_column(headers, col_mapping.get("description", []))
        qty_idx = find_column(headers, col_mapping.get("quantity", []))
        price_idx = find_column(headers, col_mapping.get("price", []))
        amount_idx = find_column(headers, col_mapping.get("amount", []))
        settle_idx = find_column(headers, col_mapping.get("settlement_date", []))
        
        # Create account
        account_id = f"csv_{institution}_{Path(file_path).stem}"
        accounts = [
            AccountDTO(
                external_id=account_id,
                name=f"{mapping['name']} Import",
                account_type=AccountType.BROKERAGE,
                account_subtype=AccountSubtype.UNKNOWN
            )
        ]
        
        # Parse transactions
        transactions: List[TransactionDTO] = []
        date_formats = mapping.get("date_formats", ["%Y-%m-%d"])
        action_mapping = mapping.get("action_mapping", {})
        
        for row_idx, row in enumerate(data_rows):
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip empty rows
            
            # Extract values
            date_str = row[date_idx] if date_idx is not None and date_idx < len(row) else None
            action_str = row[action_idx] if action_idx is not None and action_idx < len(row) else None
            symbol = row[symbol_idx] if symbol_idx is not None and symbol_idx < len(row) else None
            description = row[desc_idx] if desc_idx is not None and desc_idx < len(row) else None
            quantity = parse_number(row[qty_idx]) if qty_idx is not None and qty_idx < len(row) else None
            price = parse_number(row[price_idx]) if price_idx is not None and price_idx < len(row) else None
            amount = parse_number(row[amount_idx]) if amount_idx is not None and amount_idx < len(row) else None
            settle_date = row[settle_idx] if settle_idx is not None and settle_idx < len(row) else None
            
            # Parse date
            posted_at = parse_date(date_str, date_formats)
            if not posted_at:
                continue  # Skip rows without valid date
            
            # Map action to transaction type
            txn_type = map_action_to_type(action_str or description or "", action_mapping)
            
            # Build description
            txn_desc = description or action_str or "Transaction"
            if symbol:
                txn_desc = f"{symbol}: {txn_desc}"
            
            # Determine security type
            sec_type = SecurityType.EQUITY if symbol else None
            
            txn = TransactionDTO(
                external_id=f"csv_{row_idx}",  # Will be replaced with hash-based dedupe
                transaction_type=txn_type,
                posted_at=posted_at,
                amount=amount or 0.0,
                description=txn_desc[:200],  # Truncate long descriptions
                symbol=symbol.upper() if symbol else None,
                security_type=sec_type,
                quantity=quantity,
                price=price,
                settle_date=parse_date(settle_date, date_formats) if settle_date else None,
                raw_category=action_str
            )
            transactions.append(txn)
        
        return SyncResult(
            success=True,
            accounts=accounts,
            holdings={},  # CSV typically doesn't have holdings
            transactions={account_id: transactions},
            raw_data={
                "source": "csv_parser",
                "file_path": file_path,
                "institution": institution,
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "transactions_count": len(transactions)
            }
        )
        
    except Exception as e:
        return SyncResult(
            success=False,
            errors=[f"Failed to parse CSV file: {str(e)}"]
        )
