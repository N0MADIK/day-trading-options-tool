import { createContext, useContext, useState, ReactNode } from "react";

interface MockDataContextType {
  showMockData: boolean;
  setShowMockData: (show: boolean) => void;
}

const MockDataContext = createContext<MockDataContextType | undefined>(undefined);

export function MockDataProvider({ children }: { children: ReactNode }) {
  const [showMockData, setShowMockData] = useState(false);

  return (
    <MockDataContext.Provider value={{ showMockData, setShowMockData }}>
      {children}
    </MockDataContext.Provider>
  );
}

export function useMockData() {
  const context = useContext(MockDataContext);
  if (!context) {
    throw new Error("useMockData must be used within a MockDataProvider");
  }
  return context;
}

// Mock data for charts and graphics
export const MOCK_DATA = {
  portfolioData: [
    { date: "Jan", value: 45000 },
    { date: "Feb", value: 48500 },
    { date: "Mar", value: 47200 },
    { date: "Apr", value: 52000 },
    { date: "May", value: 58000 },
    { date: "Jun", value: 56500 },
    { date: "Jul", value: 62000 },
    { date: "Aug", value: 68000 },
    { date: "Sep", value: 71500 },
    { date: "Oct", value: 75000 },
    { date: "Nov", value: 82000 },
    { date: "Dec", value: 87500 },
  ],
  totalNetWorth: 87500,
  totalChange: 12.5,
  accounts: [
    { id: "1", institution_name: "Wells Fargo", institution_type: "bank", balance: 15000 },
    { id: "2", institution_name: "Robinhood", institution_type: "brokerage", balance: 45000 },
    { id: "3", institution_name: "Vanguard", institution_type: "retirement", balance: 27500 },
    { id: "4", institution_name: "Chase Sapphire", institution_type: "credit_card", balance: -2450 },
  ],
  recentTrades: [
    { id: "1", symbol: "AAPL", type: "BUY", shares: 10, price: 175.50, time: "Today" },
    { id: "2", symbol: "TSLA", type: "SELL", shares: 5, price: 245.00, time: "Yesterday" },
    { id: "3", symbol: "NVDA", type: "BUY", shares: 3, price: 890.25, time: "2 days ago" },
    { id: "4", symbol: "MSFT", type: "BUY", shares: 8, price: 410.00, time: "3 days ago" },
    { id: "5", symbol: "GOOGL", type: "SELL", shares: 2, price: 175.00, time: "4 days ago" },
  ],
  previousTrades: [
    { date: "12/28/2025", symbol: "AAPL", type: "BUY", amount: 1755.00, pnl: 125.50 },
    { date: "12/27/2025", symbol: "TSLA", type: "SELL", amount: 1225.00, pnl: -45.00 },
    { date: "12/26/2025", symbol: "NVDA", type: "BUY", amount: 2670.75, pnl: 340.25 },
    { date: "12/25/2025", symbol: "MSFT", type: "BUY", amount: 3280.00, pnl: 85.00 },
    { date: "12/24/2025", symbol: "GOOGL", type: "SELL", amount: 350.00, pnl: -12.00 },
  ],
  notifications: [
    { id: 1, type: "price", title: "AAPL reached $175", time: "2m ago", read: false },
    { id: 2, type: "trade", title: "Buy order executed", time: "1h ago", read: false },
    { id: 3, type: "goal", title: "75% of goal reached!", time: "Today", read: true },
  ],
  strategies: [
    { id: "1", name: "DCA Strategy", status: "active", nextRun: "Tomorrow", type: "Automated" },
    { id: "2", name: "Rebalance Portfolio", status: "paused", nextRun: "Next week", type: "Manual" },
  ],
  // Financial Breakdown mock data
  accountBreakdown: [
    { name: "Wells Fargo Checking", value: 15000, type: "bank", color: "hsl(142, 71%, 45%)" },
    { name: "Robinhood", value: 45000, type: "brokerage", color: "hsl(173, 58%, 39%)" },
    { name: "Vanguard 401k", value: 27500, type: "retirement", color: "hsl(197, 37%, 24%)" },
    { name: "Chase Sapphire", value: 2450, type: "credit_card", color: "hsl(0, 72%, 51%)" },
  ],
  spendingByCategory: [
    { category: "Housing", amount: 2500, count: 1, color: "hsl(220, 70%, 50%)", icon: "home" },
    { category: "Food", amount: 850, count: 45, color: "hsl(38, 92%, 50%)", icon: "food" },
    { category: "Transportation", amount: 450, count: 12, color: "hsl(280, 60%, 50%)", icon: "car" },
    { category: "Shopping", amount: 680, count: 23, color: "hsl(142, 71%, 45%)", icon: "shopping" },
    { category: "Entertainment", amount: 320, count: 8, color: "hsl(0, 72%, 51%)", icon: "entertainment" },
    { category: "Subscriptions", amount: 185, count: 7, color: "hsl(262, 83%, 58%)", icon: "subscription" },
    { category: "Utilities", amount: 280, count: 5, color: "hsl(173, 58%, 39%)", icon: "utilities" },
    { category: "Coffee", amount: 120, count: 28, color: "hsl(25, 95%, 53%)", icon: "coffee" },
  ],
  // Detected subscription payments
  subscriptions: [
    { id: "1", name: "Netflix", amount: 22.99, billingCycle: "monthly", category: "Entertainment", lastCharge: "2025-12-15", website: "https://netflix.com", logo: "🎬" },
    { id: "2", name: "Spotify", amount: 10.99, billingCycle: "monthly", category: "Entertainment", lastCharge: "2025-12-20", website: "https://spotify.com", logo: "🎵" },
    { id: "3", name: "Amazon Prime", amount: 14.99, billingCycle: "monthly", category: "Shopping", lastCharge: "2025-12-05", website: "https://amazon.com/prime", logo: "📦" },
    { id: "4", name: "Adobe Creative Cloud", amount: 54.99, billingCycle: "monthly", category: "Software", lastCharge: "2025-12-01", website: "https://adobe.com", logo: "🎨" },
    { id: "5", name: "OpenAI ChatGPT Plus", amount: 20.00, billingCycle: "monthly", category: "Software", lastCharge: "2025-12-18", website: "https://openai.com", logo: "🤖" },
    { id: "6", name: "iCloud+", amount: 2.99, billingCycle: "monthly", category: "Cloud Storage", lastCharge: "2025-12-10", website: "https://icloud.com", logo: "☁️" },
    { id: "7", name: "YouTube Premium", amount: 13.99, billingCycle: "monthly", category: "Entertainment", lastCharge: "2025-12-22", website: "https://youtube.com/premium", logo: "▶️" },
    { id: "8", name: "Gym Membership", amount: 45.00, billingCycle: "monthly", category: "Health", lastCharge: "2025-12-01", website: "https://planetfitness.com", logo: "🏋️" },
  ],
  // Credit card transactions for spending breakdown
  creditCardTransactions: [
    { id: "cc1", vendor: "Netflix", amount: 22.99, date: "2025-12-15", category: "Subscriptions", isRecurring: true },
    { id: "cc2", vendor: "Whole Foods", amount: 156.42, date: "2025-12-28", category: "Food", isRecurring: false },
    { id: "cc3", vendor: "Spotify", amount: 10.99, date: "2025-12-20", category: "Subscriptions", isRecurring: true },
    { id: "cc4", vendor: "Amazon", amount: 89.99, date: "2025-12-27", category: "Shopping", isRecurring: false },
    { id: "cc5", vendor: "Shell Gas", amount: 52.30, date: "2025-12-26", category: "Transportation", isRecurring: false },
    { id: "cc6", vendor: "Starbucks", amount: 6.45, date: "2025-12-28", category: "Coffee", isRecurring: false },
    { id: "cc7", vendor: "Adobe", amount: 54.99, date: "2025-12-01", category: "Subscriptions", isRecurring: true },
    { id: "cc8", vendor: "Uber Eats", amount: 34.50, date: "2025-12-25", category: "Food", isRecurring: false },
    { id: "cc9", vendor: "OpenAI", amount: 20.00, date: "2025-12-18", category: "Subscriptions", isRecurring: true },
    { id: "cc10", vendor: "Target", amount: 124.67, date: "2025-12-24", category: "Shopping", isRecurring: false },
    { id: "cc11", vendor: "Starbucks", amount: 5.95, date: "2025-12-27", category: "Coffee", isRecurring: false },
    { id: "cc12", vendor: "Amazon Prime", amount: 14.99, date: "2025-12-05", category: "Subscriptions", isRecurring: true },
    { id: "cc13", vendor: "Chipotle", amount: 15.25, date: "2025-12-23", category: "Food", isRecurring: false },
    { id: "cc14", vendor: "iCloud", amount: 2.99, date: "2025-12-10", category: "Subscriptions", isRecurring: true },
    { id: "cc15", vendor: "YouTube Premium", amount: 13.99, date: "2025-12-22", category: "Subscriptions", isRecurring: true },
  ],
  // Frequent vendors from spending
  frequentVendors: [
    { name: "Starbucks", count: 28, totalSpent: 168.50, avgTransaction: 6.02 },
    { name: "Amazon", count: 12, totalSpent: 456.78, avgTransaction: 38.07 },
    { name: "Whole Foods", count: 8, totalSpent: 892.34, avgTransaction: 111.54 },
    { name: "Uber Eats", count: 6, totalSpent: 187.50, avgTransaction: 31.25 },
    { name: "Target", count: 5, totalSpent: 412.33, avgTransaction: 82.47 },
  ],
  netWorthHistory: [
    { month: "Jul", netWorth: 62000, assets: 68000, liabilities: 6000 },
    { month: "Aug", netWorth: 68000, assets: 75000, liabilities: 7000 },
    { month: "Sep", netWorth: 72000, assets: 79000, liabilities: 7000 },
    { month: "Oct", netWorth: 76500, assets: 84000, liabilities: 7500 },
    { month: "Nov", netWorth: 82000, assets: 90000, liabilities: 8000 },
    { month: "Dec", netWorth: 87500, assets: 96000, liabilities: 8500 },
  ],
  recentTransactions: [
    { id: "1", type: "buy", symbol: "AAPL", amount: -1755.00, date: "12/28/2025", account: "Robinhood" },
    { id: "2", type: "dividend", symbol: "VTI", amount: 125.50, date: "12/27/2025", account: "Vanguard" },
    { id: "3", type: "expense", symbol: null, amount: -156.42, date: "12/28/2025", account: "Chase Sapphire", vendor: "Whole Foods" },
    { id: "4", type: "sell", symbol: "TSLA", amount: 1225.00, date: "12/26/2025", account: "Robinhood" },
    { id: "5", type: "expense", symbol: null, amount: -89.99, date: "12/27/2025", account: "Chase Sapphire", vendor: "Amazon" },
  ],
  holdings: [
    { symbol: "AAPL", name: "Apple Inc.", quantity: 25, current_price: 175.50, market_value: 4387.50, unrealized_pnl: 450.25, unrealized_pnl_percent: 11.4 },
    { symbol: "NVDA", name: "NVIDIA Corp.", quantity: 8, current_price: 890.25, market_value: 7122.00, unrealized_pnl: 1250.00, unrealized_pnl_percent: 21.3 },
    { symbol: "MSFT", name: "Microsoft Corp.", quantity: 15, current_price: 410.00, market_value: 6150.00, unrealized_pnl: 320.00, unrealized_pnl_percent: 5.5 },
    { symbol: "GOOGL", name: "Alphabet Inc.", quantity: 20, current_price: 175.00, market_value: 3500.00, unrealized_pnl: -125.00, unrealized_pnl_percent: -3.4 },
  ],
  totalPnL: 1895.25,
  totalPnLPercent: 8.7,
  totalSpending: 5385,
  // Year-over-year spending comparison
  yearOverYearSpending: [
    { month: "Jan", currentYear: 4250, previousYear: 3890, percentChange: 9.3 },
    { month: "Feb", currentYear: 3980, previousYear: 3650, percentChange: 9.0 },
    { month: "Mar", currentYear: 4520, previousYear: 4100, percentChange: 10.2 },
    { month: "Apr", currentYear: 4180, previousYear: 4350, percentChange: -3.9 },
    { month: "May", currentYear: 4650, previousYear: 4200, percentChange: 10.7 },
    { month: "Jun", currentYear: 5100, previousYear: 4800, percentChange: 6.3 },
    { month: "Jul", currentYear: 4890, previousYear: 4650, percentChange: 5.2 },
    { month: "Aug", currentYear: 5250, previousYear: 4900, percentChange: 7.1 },
    { month: "Sep", currentYear: 4780, previousYear: 4550, percentChange: 5.1 },
    { month: "Oct", currentYear: 5120, previousYear: 4780, percentChange: 7.1 },
    { month: "Nov", currentYear: 5680, previousYear: 5100, percentChange: 11.4 },
    { month: "Dec", currentYear: 5385, previousYear: 5450, percentChange: -1.2 },
  ],
  // Category comparison YoY
  categoryYoYComparison: [
    { category: "Housing", currentYear: 30000, previousYear: 28800, percentChange: 4.2 },
    { category: "Food", currentYear: 10200, previousYear: 9100, percentChange: 12.1 },
    { category: "Transportation", currentYear: 5400, previousYear: 4800, percentChange: 12.5 },
    { category: "Shopping", currentYear: 8160, previousYear: 7200, percentChange: 13.3 },
    { category: "Entertainment", currentYear: 3840, previousYear: 4200, percentChange: -8.6 },
    { category: "Subscriptions", currentYear: 2220, previousYear: 1680, percentChange: 32.1 },
    { category: "Utilities", currentYear: 3360, previousYear: 3120, percentChange: 7.7 },
    { category: "Coffee", currentYear: 1440, previousYear: 1200, percentChange: 20.0 },
  ],
};
