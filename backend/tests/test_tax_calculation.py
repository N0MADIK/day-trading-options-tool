import asyncio
import json
from datetime import datetime, date
from dataclasses import dataclass
from typing import List, Dict, Any


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


class TradePaymentAnalyzer:
    """Standalone trade payment analyzer for testing"""
    
    def calculate_trade_cost(self, trade: Trade) -> float:
        """Calculate total cost of the trade"""
        return trade.shares * trade.price
    
    def calculate_tax_on_sale(self, sold_stock: Stock, sale_price: float) -> float:
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
    
    def analyze_trade_payment(self, portfolio: Portfolio, trade: Trade) -> Dict[str, Any]:
        """Calculate the best way to pay for the trade"""
        trade_cost = self.calculate_trade_cost(trade)
        
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
            tax_on_sale = self.calculate_tax_on_sale(
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


def create_test_portfolio_with_gains() -> Portfolio:
    """Create a test portfolio with some stocks that have gains"""
    stocks = [
        Stock('AAPL', 20, 150.0, date(2023, 1, 1)),  # Long-term, potential gain
        Stock('GOOGL', 10, 1000.0, date(2023, 6, 1)),  # Long-term, potential gain
        Stock('TSLA', 5, 800.0, date(2024, 1, 1)),  # Long-term, potential gain
        Stock('AMZN', 8, 120.0, date(2024, 11, 1))   # Short-term, potential gain
    ]
    cash = 5000.0
    return Portfolio(stocks=stocks, cash=cash)


def test_tax_calculation():
    """Test tax calculation with gains"""
    
    analyzer = TradePaymentAnalyzer()
    portfolio = create_test_portfolio_with_gains()
    
    print("=" * 60)
    print("TEST: Trade with tax implications")
    print("=" * 60)
    
    # Create a trade that requires selling assets with gains
    trade = Trade('NVDA', 30, 800.0, 'buy')
    
    try:
        result = analyzer.analyze_trade_payment(portfolio, trade)
        print(f"Trade: Buy {trade.shares} shares of {trade.symbol} at ${trade.price}")
        print(f"Total cost: ${analyzer.calculate_trade_cost(trade):,.2f}")
        print(f"Available cash: ${portfolio.cash:,.2f}")
        print(f"Portfolio value: ${sum(s.shares * s.avg_price for s in portfolio.stocks) + portfolio.cash:,.2f}")
        print("\nPayment Analysis:")
        print(json.dumps(result, indent=2))
        
        # Show detailed tax calculations
        if result['assets_sold']:
            print("\nDetailed Tax Calculations:")
            for asset in result['assets_sold']:
                print(f"\n{asset['symbol']}:")
                print(f"  Shares sold: {asset['shares_sold']}")
                print(f"  Purchase price: ${asset['sale_price_per_share']:.2f}")
                print(f"  Sale price: ${asset['sale_price_per_share']:.2f}")
                print(f"  Days held: {asset['days_held']}")
                print(f"  Tax rate: {asset['tax_rate']}")
                print(f"  Tax paid: ${asset['taxes']:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_tax_calculation()
