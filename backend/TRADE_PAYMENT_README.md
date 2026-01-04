# Trade Payment Analysis API

This implementation provides a comprehensive trade payment analysis system that calculates how to pay for stock market trades, considering available cash, asset liquidation, and tax implications.

## Features

- **Cash Analysis**: Determines if available cash can cover the trade cost
- **Asset Liquidation**: Calculates which assets to sell to fund trades when cash is insufficient
- **Tax Calculations**: Computes capital gains taxes based on holding periods (long-term vs short-term)
- **Optimization**: Sells assets in tax-efficient order to minimize tax impact
- **Portfolio Integration**: Queries user holdings and bank account information

## API Endpoint

### POST `/trades/payment-analysis`

Analyzes how to pay for a trade using available cash or selling assets with tax implications.

**Request Body:**
```json
{
  "user_id": 1,
  "symbol": "NVDA",
  "shares": 50,
  "price": 800.0,
  "trade_type": "buy"
}
```

**Response:**
```json
{
  "success": true,
  "trade": {
    "symbol": "NVDA",
    "shares": 50,
    "price": 800.0,
    "total_cost": 40000.0,
    "trade_type": "BUY"
  },
  "payment_analysis": {
    "action": "sell_assets",
    "cash_used": 40000.0,
    "assets_sold": [
      {
        "symbol": "AAPL",
        "shares_sold": 20,
        "sale_price_per_share": 150.0,
        "gross_proceeds": 3000.0,
        "taxes": 450.0,
        "net_proceeds": 2550.0,
        "purchase_date": "2023-01-01",
        "days_held": 1098,
        "tax_rate": "0.15 (long-term)"
      }
    ],
    "taxes_paid": 450.0,
    "total_sold_value": 3000.0,
    "remaining_cash": 2550.0,
    "message": "Trade paid for by selling assets. Total taxes: $450.00, Remaining cash: $2,550.00"
  }
}
```

## Tax Logic

The system implements realistic tax calculations:

- **Long-term capital gains** (held > 365 days): 15% tax rate
- **Short-term capital gains** (held ≤ 365 days): 25% tax rate
- **No tax on losses**: Taxes are only calculated on profits
- **Tax optimization**: Assets are sold in order that minimizes tax impact

## Payment Strategies

### 1. Use Cash (`action: "use_cash"`)
When available cash ≥ trade cost:
- Uses cash directly
- No asset sales required
- No tax implications

### 2. Sell Assets (`action: "sell_assets"`)
When cash is insufficient but total portfolio value ≥ trade cost:
- Sells assets in tax-efficient order
- Calculates and withholds taxes
- Provides remaining cash after all transactions

### 3. Insufficient Funds (`action: "insufficient_funds"`)
When even selling all assets won't cover the trade:
- Shows maximum available funds
- Calculates shortfall amount
- Lists all assets that would need to be sold

## Implementation Details

### Service Architecture
- `TradePaymentService`: Main business logic service
- Integrates with `PersonalFinanceService` for portfolio data
- Uses existing repository pattern for data access

### Data Models
- `TradePaymentRequest`: API request schema
- `TradePaymentResponse`: API response schema
- `AssetSaleInfo`: Detailed asset sale information

### Testing
Multiple test scenarios have been implemented:
1. Cash-only payments
2. Asset liquidation with tax calculations
3. Insufficient funds scenarios
4. Mixed gains and losses

## Example Usage

```python
# API call example
import requests

response = requests.post(
    "http://localhost:8000/trades/payment-analysis",
    json={
        "user_id": 1,
        "symbol": "MSFT",
        "shares": 10,
        "price": 300.0,
        "trade_type": "buy"
    }
)

result = response.json()
print(result["payment_analysis"]["message"])
```

## Integration Notes

The service integrates with the existing personal finance system to:
- Query user holdings across all accounts
- Aggregate cash from checking/savings accounts
- Calculate cost basis for tax purposes
- Handle different purchase dates for tax calculations

This implementation provides a complete solution for trade payment analysis with realistic tax considerations and portfolio optimization.
