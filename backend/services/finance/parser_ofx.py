"""
OFX/QFX Parser

Parser for Open Financial Exchange (OFX) and Quicken (QFX) files.
Extracts accounts, transactions, and optionally positions from investment statements.
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .models import AccountType, AccountSubtype, SecurityType, TransactionType
from .connectors import SyncResult, AccountDTO, HoldingDTO, TransactionDTO


def parse_ofx_date(date_str: str) -> Optional[str]:
    """Parse OFX date format (YYYYMMDD or YYYYMMDDHHMMSS) to ISO format."""
    if not date_str:
        return None
    
    # Remove timezone info if present
    date_str = date_str.split("[")[0].strip()
    
    try:
        if len(date_str) >= 14:
            dt = datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
        elif len(date_str) >= 8:
            dt = datetime.strptime(date_str[:8], "%Y%m%d")
        else:
            return None
        
        return dt.isoformat() + "Z"
    except:
        return None


def parse_ofx_amount(amount_str: str) -> float:
    """Parse OFX amount string to float."""
    if not amount_str:
        return 0.0
    
    # Remove commas and whitespace
    clean = amount_str.replace(",", "").strip()
    
    try:
        return float(clean)
    except:
        return 0.0


def sgml_to_xml(content: str) -> str:
    """
    Convert OFX SGML format to XML for parsing.
    OFX 1.x uses SGML-like format without closing tags.
    """
    # Find the actual OFX content (skip headers)
    ofx_start = content.find("<OFX>")
    if ofx_start == -1:
        ofx_start = content.find("<ofx>")
    
    if ofx_start == -1:
        return content  # Already XML or invalid
    
    content = content[ofx_start:]
    
    # Add closing tags for self-closing elements
    # OFX uses <TAG>value instead of <TAG>value</TAG>
    lines = content.split("\n")
    result_lines = []
    tag_stack = []
    
    # Simple pattern: if a line has <TAG>value without </TAG>, add closing tag
    tag_pattern = re.compile(r"<([A-Z0-9_]+)>([^<]*)")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for opening tag with content
        match = tag_pattern.match(line)
        if match:
            tag_name = match.group(1)
            value = match.group(2).strip()
            
            if value:
                # Has value, make it self-closing
                result_lines.append(f"<{tag_name}>{value}</{tag_name}>")
            else:
                # No value, it's a container tag
                result_lines.append(f"<{tag_name}>")
                tag_stack.append(tag_name)
        elif line.startswith("</"):
            # Closing tag, pop from stack
            result_lines.append(line)
            tag_name = line[2:-1]
            if tag_stack and tag_stack[-1] == tag_name:
                tag_stack.pop()
        else:
            result_lines.append(line)
    
    # Close any remaining open tags
    while tag_stack:
        result_lines.append(f"</{tag_stack.pop()}>")
    
    return "\n".join(result_lines)


def map_ofx_transaction_type(trntype: str) -> TransactionType:
    """Map OFX transaction type to our enum."""
    trntype = trntype.upper() if trntype else ""
    
    mapping = {
        "BUY": TransactionType.BUY,
        "BUYSTOCK": TransactionType.BUY,
        "BUYMF": TransactionType.BUY,
        "BUYDEBT": TransactionType.BUY,
        "BUYOPT": TransactionType.BUY,
        "BUYOTHER": TransactionType.BUY,
        "SELL": TransactionType.SELL,
        "SELLSTOCK": TransactionType.SELL,
        "SELLMF": TransactionType.SELL,
        "SELLDEBT": TransactionType.SELL,
        "SELLOPT": TransactionType.SELL,
        "SELLOTHER": TransactionType.SELL,
        "DIV": TransactionType.DIVIDEND,
        "DIVIDEND": TransactionType.DIVIDEND,
        "CGLONG": TransactionType.DIVIDEND,  # Capital gains
        "CGSHORT": TransactionType.DIVIDEND,
        "INT": TransactionType.INTEREST,
        "INTEREST": TransactionType.INTEREST,
        "FEE": TransactionType.FEE,
        "SRVCHG": TransactionType.FEE,
        "XFER": TransactionType.TRANSFER_IN,
        "TRANSFER": TransactionType.TRANSFER_IN,
        "DEP": TransactionType.DEPOSIT,
        "DEPOSIT": TransactionType.DEPOSIT,
        "CASH": TransactionType.DEPOSIT,
        "ATM": TransactionType.WITHDRAWAL,
        "DEBIT": TransactionType.WITHDRAWAL,
        "CREDIT": TransactionType.DEPOSIT,
        "SPLIT": TransactionType.SPLIT,
    }
    
    return mapping.get(trntype, TransactionType.UNKNOWN)


def map_ofx_security_type(sectype: str) -> SecurityType:
    """Map OFX security type to our enum."""
    sectype = sectype.upper() if sectype else ""
    
    mapping = {
        "STOCK": SecurityType.EQUITY,
        "EQUITY": SecurityType.EQUITY,
        "MF": SecurityType.MUTUAL_FUND,
        "MUTUALFUND": SecurityType.MUTUAL_FUND,
        "ETF": SecurityType.ETF,
        "BOND": SecurityType.BOND,
        "DEBT": SecurityType.BOND,
        "OPT": SecurityType.OPTION,
        "OPTION": SecurityType.OPTION,
        "CASH": SecurityType.CASH,
        "MONEYMKT": SecurityType.CASH,
        "OTHER": SecurityType.UNKNOWN,
    }
    
    return mapping.get(sectype, SecurityType.UNKNOWN)


def get_element_text(element: Optional[ET.Element], path: str, default: str = "") -> str:
    """Safely get text from an XML element."""
    if element is None:
        return default
    
    child = element.find(path)
    if child is not None and child.text:
        return child.text.strip()
    return default


def parse_ofx_file(file_path: str) -> SyncResult:
    """
    Parse an OFX/QFX file and extract accounts, holdings, and transactions.
    
    Args:
        file_path: Path to the OFX/QFX file
        
    Returns:
        SyncResult with parsed data
    """
    try:
        # Read file content
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Convert SGML to XML if needed
        xml_content = sgml_to_xml(content)
        
        # Parse XML
        root = ET.fromstring(xml_content)
        
        accounts: List[AccountDTO] = []
        holdings: Dict[str, List[HoldingDTO]] = {}
        transactions: Dict[str, List[TransactionDTO]] = {}
        securities_map: Dict[str, Tuple[str, SecurityType]] = {}  # secid -> (symbol, type)
        
        # Find all statement responses (bank, credit card, investment)
        for stmtrs in root.iter():
            # Process bank/credit card statements
            if stmtrs.tag in ("STMTRS", "CCSTMTRS"):
                acct_from = stmtrs.find(".//ACCTFROM") or stmtrs.find(".//BANKACCTFROM") or stmtrs.find(".//CCACCTFROM")
                
                if acct_from:
                    acct_id = get_element_text(acct_from, "ACCTID", "unknown")
                    acct_type_str = get_element_text(acct_from, "ACCTTYPE", "CHECKING")
                    
                    # Determine account type
                    if stmtrs.tag == "CCSTMTRS":
                        acct_type = AccountType.CASH
                        acct_subtype = AccountSubtype.UNKNOWN
                    elif "SAVINGS" in acct_type_str.upper():
                        acct_type = AccountType.CASH
                        acct_subtype = AccountSubtype.SAVINGS
                    else:
                        acct_type = AccountType.CASH
                        acct_subtype = AccountSubtype.CHECKING
                    
                    account = AccountDTO(
                        external_id=acct_id,
                        name=f"Account {acct_id[-4:]}",
                        account_type=acct_type,
                        account_subtype=acct_subtype,
                        masked_number=f"****{acct_id[-4:]}" if len(acct_id) >= 4 else acct_id
                    )
                    accounts.append(account)
                    transactions[acct_id] = []
                    
                    # Process transactions
                    for stmttrn in stmtrs.findall(".//STMTTRN"):
                        fitid = get_element_text(stmttrn, "FITID")
                        trntype = get_element_text(stmttrn, "TRNTYPE")
                        dtposted = get_element_text(stmttrn, "DTPOSTED")
                        trnamt = get_element_text(stmttrn, "TRNAMT")
                        name = get_element_text(stmttrn, "NAME")
                        memo = get_element_text(stmttrn, "MEMO")
                        
                        txn = TransactionDTO(
                            external_id=fitid,
                            transaction_type=map_ofx_transaction_type(trntype),
                            posted_at=parse_ofx_date(dtposted) or datetime.utcnow().isoformat() + "Z",
                            amount=parse_ofx_amount(trnamt),
                            description=name or memo or "Transaction",
                            raw_category=trntype
                        )
                        transactions[acct_id].append(txn)
            
            # Process investment statements
            elif stmtrs.tag == "INVSTMTRS":
                acct_from = stmtrs.find(".//INVACCTFROM")
                
                if acct_from:
                    acct_id = get_element_text(acct_from, "ACCTID", "unknown")
                    broker_id = get_element_text(acct_from, "BROKERID", "")
                    
                    account = AccountDTO(
                        external_id=acct_id,
                        name=f"Investment {acct_id[-4:]}",
                        account_type=AccountType.BROKERAGE,
                        account_subtype=AccountSubtype.TAXABLE,
                        masked_number=f"****{acct_id[-4:]}" if len(acct_id) >= 4 else acct_id
                    )
                    accounts.append(account)
                    holdings[acct_id] = []
                    transactions[acct_id] = []
                    
                    # Process security list first
                    seclist = root.find(".//SECLIST")
                    if seclist:
                        for secinfo in seclist.findall(".//SECINFO"):
                            secid = get_element_text(secinfo, ".//SECID/UNIQUEID")
                            ticker = get_element_text(secinfo, ".//TICKER")
                            sectype = get_element_text(secinfo, ".//SECTYPE", "STOCK")
                            
                            if secid:
                                securities_map[secid] = (ticker or secid, map_ofx_security_type(sectype))
                    
                    # Process positions/holdings
                    invposlist = stmtrs.find(".//INVPOSLIST")
                    if invposlist:
                        for posstock in invposlist.findall(".//POSSTOCK") + invposlist.findall(".//POSMF") + invposlist.findall(".//POSOTHER"):
                            invpos = posstock.find("INVPOS")
                            if invpos:
                                secid = get_element_text(invpos, "SECID/UNIQUEID")
                                units = parse_ofx_amount(get_element_text(invpos, "UNITS"))
                                unitprice = parse_ofx_amount(get_element_text(invpos, "UNITPRICE"))
                                mktval = parse_ofx_amount(get_element_text(invpos, "MKTVAL"))
                                
                                symbol, sec_type = securities_map.get(secid, (secid, SecurityType.UNKNOWN))
                                
                                holding = HoldingDTO(
                                    symbol=symbol,
                                    security_name=symbol,  # Would need security list for full name
                                    security_type=sec_type,
                                    quantity=units,
                                    price=unitprice,
                                    value=mktval or (units * unitprice if unitprice else None)
                                )
                                holdings[acct_id].append(holding)
                    
                    # Process investment transactions
                    invtranlist = stmtrs.find(".//INVTRANLIST")
                    if invtranlist:
                        for inv_txn in invtranlist:
                            if inv_txn.tag in ("BUYSTOCK", "SELLSTOCK", "BUYMF", "SELLMF", "INCOME", "REINVEST"):
                                invtran = inv_txn.find(".//INVTRAN")
                                if invtran:
                                    fitid = get_element_text(invtran, "FITID")
                                    dttrade = get_element_text(invtran, "DTTRADE")
                                    
                                    secid = get_element_text(inv_txn, ".//SECID/UNIQUEID")
                                    units = parse_ofx_amount(get_element_text(inv_txn, "UNITS", "0"))
                                    unitprice = parse_ofx_amount(get_element_text(inv_txn, "UNITPRICE", "0"))
                                    total = parse_ofx_amount(get_element_text(inv_txn, "TOTAL", "0"))
                                    
                                    symbol, sec_type = securities_map.get(secid, (secid, SecurityType.UNKNOWN))
                                    
                                    txn = TransactionDTO(
                                        external_id=fitid,
                                        transaction_type=map_ofx_transaction_type(inv_txn.tag),
                                        posted_at=parse_ofx_date(dttrade) or datetime.utcnow().isoformat() + "Z",
                                        amount=total,
                                        description=f"{inv_txn.tag} {symbol}",
                                        symbol=symbol,
                                        security_type=sec_type,
                                        quantity=units,
                                        price=unitprice,
                                        trade_date=parse_ofx_date(dttrade),
                                        raw_category=inv_txn.tag
                                    )
                                    transactions[acct_id].append(txn)
        
        return SyncResult(
            success=True,
            accounts=accounts,
            holdings=holdings,
            transactions=transactions,
            raw_data={
                "source": "ofx_parser",
                "file_path": file_path,
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "accounts_count": len(accounts),
                "holdings_count": sum(len(h) for h in holdings.values()),
                "transactions_count": sum(len(t) for t in transactions.values())
            }
        )
        
    except Exception as e:
        return SyncResult(
            success=False,
            errors=[f"Failed to parse OFX file: {str(e)}"]
        )
