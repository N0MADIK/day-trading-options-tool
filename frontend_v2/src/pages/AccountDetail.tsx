import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Clock,
  FileText,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPie,
  Pie,
  Cell,
} from "recharts";
import { toast } from "@/hooks/use-toast";

// Mock data for accounts
const accountsData: Record<string, any> = {
  robinhood: {
    name: "Robinhood",
    type: "Brokerage",
    logo: "🏹",
    balance: 85420.50,
    change: 2.45,
    lastSync: "2 minutes ago",
    accountNumber: "****4521",
    holdings: [
      { symbol: "AAPL", name: "Apple Inc.", shares: 50, value: 8925, change: 1.2 },
      { symbol: "TSLA", name: "Tesla Inc.", shares: 30, value: 7455, change: 3.5 },
      { symbol: "NVDA", name: "NVIDIA Corp.", shares: 20, value: 9904, change: 2.1 },
      { symbol: "GOOGL", name: "Alphabet Inc.", shares: 25, value: 3545, change: -0.8 },
      { symbol: "MSFT", name: "Microsoft Corp.", shares: 40, value: 15156, change: 0.9 },
    ],
    transactions: [
      { date: "2024-01-02", type: "BUY", symbol: "AAPL", shares: 10, amount: 1785, status: "completed" },
      { date: "2024-01-01", type: "SELL", symbol: "TSLA", shares: 5, amount: 1241.50, status: "completed" },
      { date: "2023-12-29", type: "DIVIDEND", symbol: "MSFT", shares: 0, amount: 45.20, status: "completed" },
      { date: "2023-12-28", type: "BUY", symbol: "NVDA", shares: 5, amount: 2476, status: "completed" },
    ],
    performance: [
      { month: "Jul", value: 72000 },
      { month: "Aug", value: 75500 },
      { month: "Sep", value: 71200 },
      { month: "Oct", value: 78900 },
      { month: "Nov", value: 82300 },
      { month: "Dec", value: 85420 },
    ],
    allocation: [
      { name: "Technology", value: 65, color: "hsl(142, 71%, 45%)" },
      { name: "Healthcare", value: 15, color: "hsl(173, 58%, 39%)" },
      { name: "Finance", value: 12, color: "hsl(38, 92%, 50%)" },
      { name: "Energy", value: 8, color: "hsl(197, 37%, 24%)" },
    ],
  },
  "chase": {
    name: "Chase",
    type: "Bank",
    logo: "🏦",
    balance: 12350.00,
    change: 0,
    lastSync: "1 hour ago",
    accountNumber: "****7892",
    holdings: [],
    transactions: [
      { date: "2024-01-02", type: "DEPOSIT", symbol: "", shares: 0, amount: 3500, status: "completed" },
      { date: "2024-01-01", type: "WITHDRAWAL", symbol: "", shares: 0, amount: 200, status: "completed" },
      { date: "2023-12-30", type: "TRANSFER", symbol: "", shares: 0, amount: 1000, status: "completed" },
      { date: "2023-12-28", type: "PAYMENT", symbol: "", shares: 0, amount: 150.50, status: "completed" },
    ],
    performance: [
      { month: "Jul", value: 10500 },
      { month: "Aug", value: 11200 },
      { month: "Sep", value: 9800 },
      { month: "Oct", value: 10900 },
      { month: "Nov", value: 11800 },
      { month: "Dec", value: 12350 },
    ],
    allocation: [],
  },
  vanguard: {
    name: "Vanguard",
    type: "Brokerage",
    logo: "⛵",
    balance: 156780.25,
    change: 1.87,
    lastSync: "30 minutes ago",
    accountNumber: "****3456",
    holdings: [
      { symbol: "VTI", name: "Vanguard Total Stock Market ETF", shares: 200, value: 45600, change: 0.8 },
      { symbol: "VXUS", name: "Vanguard Total International Stock ETF", shares: 150, value: 8250, change: -0.3 },
      { symbol: "BND", name: "Vanguard Total Bond Market ETF", shares: 300, value: 22500, change: 0.1 },
      { symbol: "VGT", name: "Vanguard Information Technology ETF", shares: 50, value: 25430, change: 1.5 },
    ],
    transactions: [
      { date: "2024-01-02", type: "BUY", symbol: "VTI", shares: 10, amount: 2280, status: "completed" },
      { date: "2023-12-15", type: "DIVIDEND", symbol: "VTI", shares: 0, amount: 312.50, status: "completed" },
      { date: "2023-12-01", type: "BUY", symbol: "BND", shares: 25, amount: 1875, status: "completed" },
    ],
    performance: [
      { month: "Jul", value: 142000 },
      { month: "Aug", value: 145500 },
      { month: "Sep", value: 140200 },
      { month: "Oct", value: 148900 },
      { month: "Nov", value: 153300 },
      { month: "Dec", value: 156780 },
    ],
    allocation: [
      { name: "US Stocks", value: 55, color: "hsl(142, 71%, 45%)" },
      { name: "International", value: 20, color: "hsl(173, 58%, 39%)" },
      { name: "Bonds", value: 18, color: "hsl(38, 92%, 50%)" },
      { name: "Tech Sector", value: 7, color: "hsl(197, 37%, 24%)" },
    ],
  },
};

// Default data for unrecognized accounts
const defaultAccountData = {
  name: "Account",
  type: "Unknown",
  logo: "💼",
  balance: 0,
  change: 0,
  lastSync: "Never",
  accountNumber: "****0000",
  holdings: [],
  transactions: [],
  performance: [],
  allocation: [],
};

export default function AccountDetail() {
  const { accountId } = useParams<{ accountId: string }>();
  const account = accountsData[accountId || ""] || { ...defaultAccountData, name: accountId };

  const handleSync = () => {
    toast({
      title: "Syncing...",
      description: `Fetching latest data from ${account.name}`,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/connections">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-lg bg-secondary flex items-center justify-center text-3xl">
              {account.logo}
            </div>
            <div>
              <h1 className="text-2xl font-bold">{account.name}</h1>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Badge variant="outline">{account.type}</Badge>
                <span className="text-sm">Account {account.accountNumber}</span>
              </div>
            </div>
          </div>
        </div>
        <Button onClick={handleSync}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Sync Now
        </Button>
      </div>

      {/* Balance Card */}
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-card to-primary/5">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Account Balance</p>
              <h2 className="text-4xl font-bold">
                ${account.balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </h2>
              {account.change !== 0 && (
                <div className="flex items-center gap-2 mt-2">
                  <Badge
                    variant="outline"
                    className={
                      account.change >= 0
                        ? "border-primary text-primary"
                        : "border-destructive text-destructive"
                    }
                  >
                    {account.change >= 0 ? (
                      <ArrowUpRight className="h-3 w-3 mr-1" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3 mr-1" />
                    )}
                    {Math.abs(account.change)}%
                  </Badge>
                  <span className="text-sm text-muted-foreground">this month</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              Last synced {account.lastSync}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {account.holdings.length > 0 && (
            <TabsTrigger value="holdings">Holdings</TabsTrigger>
          )}
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6 space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Performance Chart */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                {account.performance.length > 0 ? (
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={account.performance}>
                        <defs>
                          <linearGradient id="colorPerf" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
                        <XAxis dataKey="month" stroke="hsl(220, 10%, 55%)" fontSize={12} />
                        <YAxis
                          stroke="hsl(220, 10%, 55%)"
                          fontSize={12}
                          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(220, 18%, 10%)",
                            border: "1px solid hsl(220, 15%, 20%)",
                            borderRadius: "8px",
                          }}
                          formatter={(value: number) => [`$${value.toLocaleString()}`, "Value"]}
                        />
                        <Area
                          type="monotone"
                          dataKey="value"
                          stroke="hsl(142, 71%, 45%)"
                          strokeWidth={2}
                          fillOpacity={1}
                          fill="url(#colorPerf)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                    No performance data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Allocation Chart */}
            {account.allocation.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-primary" />
                    Allocation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[180px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPie>
                        <Pie
                          data={account.allocation}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={70}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {account.allocation.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(220, 18%, 10%)",
                            border: "1px solid hsl(220, 15%, 20%)",
                            borderRadius: "8px",
                          }}
                          formatter={(value: number) => [`${value}%`, "Allocation"]}
                        />
                      </RechartsPie>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2 mt-4">
                    {account.allocation.map((item: any) => (
                      <div key={item.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: item.color }}
                          />
                          <span className="text-sm">{item.name}</span>
                        </div>
                        <span className="text-sm font-medium">{item.value}%</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {account.holdings.length > 0 && (
          <TabsContent value="holdings" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-primary" />
                  Holdings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Symbol</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Name</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Shares</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Value</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {account.holdings.map((holding: any) => (
                        <tr
                          key={holding.symbol}
                          className="border-b border-border/50 hover:bg-secondary/50 transition-colors"
                        >
                          <td className="py-3 px-4 font-mono font-bold text-primary">
                            {holding.symbol}
                          </td>
                          <td className="py-3 px-4 text-muted-foreground">{holding.name}</td>
                          <td className="py-3 px-4 text-right">{holding.shares}</td>
                          <td className="py-3 px-4 text-right font-medium">
                            ${holding.value.toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <span
                              className={`flex items-center justify-end gap-1 ${
                                holding.change >= 0 ? "text-primary" : "text-destructive"
                              }`}
                            >
                              {holding.change >= 0 ? (
                                <TrendingUp className="h-4 w-4" />
                              ) : (
                                <TrendingDown className="h-4 w-4" />
                              )}
                              {holding.change >= 0 ? "+" : ""}
                              {holding.change}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="transactions" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Recent Transactions
              </CardTitle>
            </CardHeader>
            <CardContent>
              {account.transactions.length > 0 ? (
                <div className="space-y-3">
                  {account.transactions.map((tx: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-4 rounded-lg bg-secondary/50"
                    >
                      <div className="flex items-center gap-4">
                        <Badge
                          variant="outline"
                          className={
                            tx.type === "BUY" || tx.type === "DEPOSIT"
                              ? "border-primary text-primary"
                              : tx.type === "SELL" || tx.type === "WITHDRAWAL"
                              ? "border-destructive text-destructive"
                              : "border-muted-foreground"
                          }
                        >
                          {tx.type}
                        </Badge>
                        <div>
                          {tx.symbol && (
                            <p className="font-mono font-bold">{tx.symbol}</p>
                          )}
                          <p className="text-sm text-muted-foreground">{tx.date}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">
                          {tx.type === "SELL" || tx.type === "WITHDRAWAL" ? "-" : "+"}$
                          {tx.amount.toLocaleString()}
                        </p>
                        {tx.shares > 0 && (
                          <p className="text-sm text-muted-foreground">{tx.shares} shares</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-muted-foreground">
                  No transactions found
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
