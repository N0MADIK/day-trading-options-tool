import asyncio
import json
from datetime import datetime, date
from app.services.trade_payment_service import TradePaymentService
from app.services.personal_finance_service import PersonalFinanceService


class MockPersonalFinanceService:
    """Mock personal finance service for testing"""
    
    async def list_holdings(self, request):
        """Return mock holdings data"""
        return {
            'holdings': [
                {
                    'security_symbol': 'AAPL',
                    'quantity': 20,
                    'avg_cost_basis': 150.0,
                    'purchase_date': '2023-01-01'
                },
                {
                    'security_symbol': 'GOOGL',
                    'quantity': 10,
                    'avg_cost_basis': 2000.0,
                    'purchase_date': '2023-06-01'
                },
                {
                    'security_symbol': 'TSLA',
                    'quantity': 5,
                    'avg_cost_basis': 500.0,
                    'purchase_date': '2024-01-01'
                },
                {
                    'security_symbol': 'AMZN',
                    'quantity': 8,
                    'avg_cost_basis': 100.0,
                    'purchase_date': '2023-12-01'
                }
            ]
        }
    
    async def list_accounts(self, request):
        """Return mock account data"""
        return {
            'accounts': [
                {
                    'account_type': 'CASH',
                    'balance': 5000.0
                },
                {
                    'account_type': 'CHECKING',
                    'balance': 2000.0
                }
            ]
        }


async def test_trade_payment_analysis():
    """Test the trade payment analysis with sample data"""
    
    # Create mock service
    mock_pf_service = MockPersonalFinanceService()
    payment_service = TradePaymentService(mock_pf_service)
    
    # Test case 1: Trade that can be paid with cash
    print("=" * 60)
    print("TEST 1: Trade that can be paid with available cash")
    print("=" * 60)
    
    trade_info_1 = {
        'symbol': 'MSFT',
        'shares': 10,
        'price': 300.0,
        'trade_type': 'buy'
    }
    
    try:
        result_1 = await payment_service.analyze_trade_payment(1, trade_info_1)
        print(json.dumps(result_1, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test case 2: Trade that requires selling assets
    print("\n" + "=" * 60)
    print("TEST 2: Trade that requires selling assets")
    print("=" * 60)
    
    trade_info_2 = {
        'symbol': 'NVDA',
        'shares': 50,
        'price': 800.0,
        'trade_type': 'buy'
    }
    
    try:
        result_2 = await payment_service.analyze_trade_payment(1, trade_info_2)
        print(json.dumps(result_2, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test case 3: Large trade that exceeds all available funds
    print("\n" + "=" * 60)
    print("TEST 3: Trade that exceeds all available funds")
    print("=" * 60)
    
    trade_info_3 = {
        'symbol': 'BRKA',
        'shares': 100,
        'price': 5000.0,
        'trade_type': 'buy'
    }
    
    try:
        result_3 = await payment_service.analyze_trade_payment(1, trade_info_3)
        print(json.dumps(result_3, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test case 4: Sell trade (should not require selling assets)
    print("\n" + "=" * 60)
    print("TEST 4: Sell trade")
    print("=" * 60)
    
    trade_info_4 = {
        'symbol': 'AAPL',
        'shares': 5,
        'price': 180.0,
        'trade_type': 'sell'
    }
    
    try:
        result_4 = await payment_service.analyze_trade_payment(1, trade_info_4)
        print(json.dumps(result_4, indent=2))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_trade_payment_analysis())
