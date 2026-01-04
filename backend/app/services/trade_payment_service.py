from typing import List, Dict, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass

from app.services.personal_finance_service import PersonalFinanceService
from app.domain.errors import NotFoundError, ValidationError


@dataclass
class Stock:
    """Stock holding representation"""
    symbol: str
    shares: int
    avg_price: float
    purchase_date: date


@dataclass
class Trade:
    """Trade representation"""
    symbol: str
    shares: int
    price: float
    trade_type: str  # 'buy' or 'sell'


@dataclass
class Portfolio:
    """Portfolio representation"""
    stocks: List[Stock]
    cash: float


class TradePaymentService:
    """Service for calculating trade payment methods with tax considerations"""
    
    def __init__(self, personal_finance_service: PersonalFinanceService):
        self.pf_service = personal_finance_service
    
    async def analyze_trade_payment(self, user_id: int, trade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how to pay for a trade using available cash or selling assets
        
        Args:
            user_id: The user ID
            trade_info: Dictionary containing trade details (symbol, shares, price, trade_type)
            
        Returns:
            Dictionary with payment analysis including assets to sell and tax implications
        """
        try:
            # Validate trade info
            required_fields = ['symbol', 'shares', 'price', 'trade_type']
            for field in required_fields:
                if field not in trade_info:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Create trade object
            trade = Trade(
                symbol=trade_info['symbol'],
                shares=trade_info['shares'],
                price=trade_info['price'],
                trade_type=trade_info['trade_type']
            )
            
            # Get user's portfolio data
            portfolio = await self._get_user_portfolio(user_id)
            
            # Calculate payment method
            payment_analysis = self._calculate_payment_method(portfolio, trade)
            
            return {
                "success": True,
                "trade": {
                    "symbol": trade.symbol,
                    "shares": trade.shares,
                    "price": trade.price,
                    "total_cost": self._calculate_trade_cost(trade),
                    "trade_type": trade.trade_type
                },
                "payment_analysis": payment_analysis
            }
            
        except Exception as e:
            raise e
    
    async def _get_user_portfolio(self, user_id: int) -> Portfolio:
        """Get user's portfolio including holdings and cash"""
        try:
            # Get user's holdings
            holdings_request = {
                "user_id": user_id,
                "limit": 1000
            }
            holdings_response = await self.pf_service.list_holdings(holdings_request)
            
            # Get user's accounts (for cash)
            accounts_request = {
                "user_id": user_id,
                "limit": 1000
            }
            accounts_response = await self.pf_service.list_accounts(accounts_request)
            
            # Process holdings into Stock objects
            stocks = []
            for holding in holdings_response.get('holdings', []):
                # Calculate average purchase price and get earliest purchase date
                avg_price = holding.get('avg_cost_basis', 0)
                purchase_date = self._parse_date(holding.get('purchase_date', date.today()))
                
                stock = Stock(
                    symbol=holding.get('security_symbol', ''),
                    shares=holding.get('quantity', 0),
                    avg_price=avg_price,
                    purchase_date=purchase_date
                )
                stocks.append(stock)
            
            # Calculate total cash from cash accounts
            total_cash = 0.0
            for account in accounts_response.get('accounts', []):
                if account.get('account_type') in ['CASH', 'CHECKING', 'SAVINGS']:
                    total_cash += account.get('balance', 0)
            
            return Portfolio(stocks=stocks, cash=total_cash)
            
        except Exception as e:
            # If we can't get portfolio data, return empty portfolio
            return Portfolio(stocks=[], cash=0.0)
    
    def _parse_date(self, date_input) -> date:
        """Parse date from various formats"""
        if isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, str):
            try:
                return datetime.fromisoformat(date_input.replace('Z', '+00:00')).date()
            except:
                return date.today()
        else:
            return date.today()
    
    def _calculate_trade_cost(self, trade: Trade) -> float:
        """Calculate total cost of the trade"""
        return trade.shares * trade.price
    
    def _calculate_tax_on_sale(self, sold_stock: Stock, sale_price: float) -> float:
        """Calculate tax on stock sale based on holding period"""
        purchase_date = sold_stock.purchase_date
        current_date = date.today()
        
        days_held = (current_date - purchase_date).days
        
        if days_held > 365:  # Long-term capital gains
            tax_rate = 0.15
        else:  # Short-term capital gains
            tax_rate = 0.25
        
        profit = (sale_price - sold_stock.avg_price) * sold_stock.shares
        tax = profit * tax_rate
        return max(0, tax)  # Ensure we don't return negative taxes
    
    def _calculate_payment_method(self, portfolio: Portfolio, trade: Trade) -> Dict[str, Any]:
        """Calculate the best way to pay for the trade"""
        trade_cost = self._calculate_trade_cost(trade)
        
        # If we have enough cash, no need to sell anything
        if portfolio.cash >= trade_cost:
            return {
                'action': 'use_cash',
                'cash_used': trade_cost,
                'assets_sold': [],
                'taxes_paid': 0,
                'remaining_cash': portfolio.cash - trade_cost,
                'message': f'Trade can be paid for with available cash. Remaining cash: ${portfolio.cash - trade_cost:,.2f}'
            }
        
        # We need to sell some assets
        assets_to_sell = []
        total_sold_value = 0
        total_taxes = 0
        
        # Strategy: Sell the stocks that will incur the least tax
        # Sort by avg_price (ascending) to sell cheapest stocks first to minimize taxes
        sorted_stocks = sorted(
            portfolio.stocks,
            key=lambda x: x.avg_price,
            reverse=False
        )
        
        for stock in sorted_stocks:
            if total_sold_value >= trade_cost:
                break
            
            # Calculate how many shares to sell to cover the remaining cost
            remaining_amount_needed = trade_cost - total_sold_value
            
            # We can sell all shares of this stock or just enough to cover the rest
            shares_to_sell = min(stock.shares, int(remaining_amount_needed / stock.avg_price) + 1)
            
            if shares_to_sell <= 0:
                continue
            
            # Calculate tax on this sale
            tax_on_sale = self._calculate_tax_on_sale(
                Stock(stock.symbol, shares_to_sell, stock.avg_price, stock.purchase_date),
                stock.avg_price
            )
            
            # Add to assets to sell
            assets_to_sell.append({
                'symbol': stock.symbol,
                'shares_sold': shares_to_sell,
                'sale_price_per_share': stock.avg_price,
                'gross_proceeds': shares_to_sell * stock.avg_price,
                'taxes': tax_on_sale,
                'net_proceeds': shares_to_sell * stock.avg_price - tax_on_sale,
                'purchase_date': stock.purchase_date.isoformat(),
                'days_held': (date.today() - stock.purchase_date).days,
                'tax_rate': '0.15 (long-term)' if (date.today() - stock.purchase_date).days > 365 else '0.25 (short-term)'
            })
            
            total_sold_value += shares_to_sell * stock.avg_price
            total_taxes += tax_on_sale
        
        # Calculate remaining cash after selling assets and paying for trade
        remaining_cash = portfolio.cash + total_sold_value - trade_cost - total_taxes
        
        # Check if we have enough assets to cover the trade
        if total_sold_value < trade_cost:
            return {
                'action': 'insufficient_funds',
                'cash_available': portfolio.cash,
                'total_asset_value': total_sold_value,
                'trade_cost': trade_cost,
                'shortfall': trade_cost - (portfolio.cash + total_sold_value),
                'assets_sold': assets_to_sell,
                'taxes_paid': total_taxes,
                'message': f'Insufficient funds to cover trade. Shortfall: ${trade_cost - (portfolio.cash + total_sold_value):,.2f}'
            }
        
        return {
            'action': 'sell_assets',
            'cash_used': trade_cost,
            'assets_sold': assets_to_sell,
            'taxes_paid': total_taxes,
            'total_sold_value': total_sold_value,
            'remaining_cash': remaining_cash,
            'message': f'Trade paid for by selling assets. Total taxes: ${total_taxes:,.2f}, Remaining cash: ${remaining_cash:,.2f}'
        }
