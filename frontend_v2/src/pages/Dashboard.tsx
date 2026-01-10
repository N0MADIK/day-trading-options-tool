import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp,
  DollarSign,
  Bell,
  MessageSquare,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  ChevronRight,
  Settings,
  BellRing,
  Send,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useAuth } from "@/hooks/useAuth";
import { useConnections } from "@/hooks/useConnections";
import { useMockData, MOCK_DATA } from "@/hooks/useMockData";
import { api } from "@/lib/api";
import { DataPlaceholder } from "@/components/ui/DataPlaceholder";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { accounts, holdings, transactions, totalNetWorth, loading: connectionsLoading } = useConnections();
  const { showMockData } = useMockData();
  const [notificationSettings, setNotificationSettings] = useState({
    priceAlerts: true,
    tradeExecutions: true,
    goalProgress: true,
    dailySummary: false,
  });
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loadingSettings, setLoadingSettings] = useState(true);

  // Use mock data if toggle is on, otherwise use real data
  const hasConnectedAccounts = showMockData || accounts.length > 0;
  const hasHoldings = showMockData || holdings.length > 0;
  const hasTransactions = showMockData || transactions.length > 0;
  const displayNetWorth = showMockData ? MOCK_DATA.totalNetWorth : totalNetWorth;

  // Fetch notification settings and strategies from API
  useEffect(() => {
    if (!user) return;

    const fetchData = async () => {
      try {
        // Fetch notification settings
        const settings = await api.get<{
          price_alerts?: boolean;
          email_notifications?: boolean;
          goal_progress_alerts?: boolean;
          daily_summary?: boolean;
        }>('/notification-settings').catch(() => null);

        if (settings) {
          setNotificationSettings({
            priceAlerts: settings.price_alerts || false,
            tradeExecutions: settings.email_notifications || false,
            goalProgress: settings.goal_progress_alerts || false,
            dailySummary: settings.daily_summary || false,
          });
        }

        // Fetch trading strategies
        const strats = await api.get<any[]>('/trading-strategies').catch(() => []);
        setStrategies(strats || []);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoadingSettings(false);
      }
    };

    fetchData();
  }, [user]);

  // Update notification settings via API
  const updateNotificationSetting = async (key: string, value: boolean) => {
    if (!user) return;

    setNotificationSettings(prev => ({ ...prev, [key]: value }));

    const columnMap: Record<string, string> = {
      priceAlerts: 'price_alerts',
      tradeExecutions: 'email_notifications',
      goalProgress: 'goal_progress_alerts',
      dailySummary: 'daily_summary',
    };

    try {
      await api.put('/notification-settings', { [columnMap[key]]: value });
    } catch (error) {
      console.error('Error updating notification setting:', error);
    }
  };

  // Generate portfolio chart data (mock or real)
  const portfolioData = showMockData
    ? MOCK_DATA.portfolioData
    : (() => {
      if (accounts.length === 0) return [];

      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const baseValue = totalNetWorth > 0 ? totalNetWorth * 0.6 : 0;
      const growth = totalNetWorth > 0 ? (totalNetWorth - baseValue) / 12 : 0;

      return months.map((month, idx) => ({
        date: month,
        value: Math.round(baseValue + (growth * idx) + (Math.random() - 0.5) * growth * 0.5),
      }));
    })();

  // Get recent trades (mock or real)
  const recentTrades = showMockData
    ? MOCK_DATA.recentTrades
    : (transactions.length > 0
      ? transactions
        .filter(t => t.symbol && (t.transaction_type === 'buy' || t.transaction_type === 'sell'))
        .slice(0, 5)
        .map(t => ({
          id: t.id,
          symbol: t.symbol || '',
          type: t.transaction_type.toUpperCase(),
          shares: t.quantity || 0,
          price: t.price || 0,
          time: new Date(t.transaction_date).toLocaleDateString(),
        }))
      : []);

  // Get previous trades for table (mock or real)
  const previousTrades = showMockData
    ? MOCK_DATA.previousTrades
    : (transactions.length > 0
      ? transactions.slice(0, 5).map(t => ({
        date: new Date(t.transaction_date).toLocaleDateString(),
        symbol: t.symbol || 'TRANSFER',
        type: t.transaction_type.toUpperCase(),
        amount: t.total_amount,
        pnl: t.symbol ? (Math.random() > 0.5 ? Math.random() * 500 : -Math.random() * 100) : 0,
      }))
      : []);

  // Format trading strategies for display (mock or real)
  const displayStrategies = showMockData
    ? MOCK_DATA.strategies
    : (strategies.length > 0 ? strategies.map(s => ({
      id: s.id,
      name: s.name,
      status: s.is_active ? 'active' : 'paused',
      nextRun: s.next_execution_at ? new Date(s.next_execution_at).toLocaleDateString() : 'Not scheduled',
      type: s.is_automated ? 'Automated' : 'Manual',
    })) : []);

  const displayAccounts = showMockData ? MOCK_DATA.accounts : accounts;

  const notifications = showMockData
    ? MOCK_DATA.notifications
    : [
      ...(accounts.length > 0 ? [{ id: 1, type: "sync", title: `${accounts[0].institution_name} connected`, time: "Recently", read: false }] : []),
      ...(transactions.length > 0 ? [{ id: 2, type: "trade", title: `${transactions.length} transactions synced`, time: "Today", read: true }] : []),
      ...(holdings.length > 0 ? [{ id: 3, type: "goal", title: `${holdings.length} holdings tracked`, time: "Today", read: true }] : []),
    ];

  const totalChange = showMockData
    ? MOCK_DATA.totalChange
    : (accounts.length > 0 && portfolioData.length > 1
      ? ((portfolioData[11]?.value - portfolioData[0]?.value) / portfolioData[0]?.value * 100)
      : 0);

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <DollarSign className="h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold mb-2">Welcome to Finance Monkey 🐵</h2>
        <p className="text-muted-foreground mb-4">Sign in to make line go up!</p>
        <Button onClick={() => navigate('/auth')}>Sign In</Button>
      </div>
    );
  }

  const isLoading = connectionsLoading || loadingSettings;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's your financial overview
        </p>
      </div>

      {/* Net Worth & Portfolio Chart Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Net Worth Card */}
        <Card className="border-2 border-primary/20 bg-gradient-to-br from-card to-primary/5">
          <CardContent className="p-6">
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-6 w-32" />
              </div>
            ) : hasConnectedAccounts ? (
              <div className="flex flex-col gap-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Total Net Worth</p>
                  <h2 className="text-3xl md:text-4xl font-bold">
                    ${displayNetWorth.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </h2>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge
                      variant="outline"
                      className={`${totalChange >= 0
                        ? "border-primary text-primary"
                        : "border-destructive text-destructive"
                        }`}
                    >
                      {totalChange >= 0 ? (
                        <ArrowUpRight className="h-3 w-3 mr-1" />
                      ) : (
                        <ArrowDownRight className="h-3 w-3 mr-1" />
                      )}
                      {Math.abs(totalChange).toFixed(2)}%
                    </Badge>
                    <span className="text-sm text-muted-foreground">this month</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-10 w-10 text-primary opacity-50" />
                  <span className="text-sm text-muted-foreground">
                    {displayAccounts.length} account{displayAccounts.length !== 1 ? 's' : ''} connected
                  </span>
                </div>
              </div>
            ) : (
              <DataPlaceholder
                title="No Accounts Connected"
                description="Connect a bank or brokerage account to see your net worth"
                className="min-h-[150px]"
              />
            )}
          </CardContent>
        </Card>

        {/* Portfolio Chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Portfolio Performance</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[180px] w-full" />
            ) : hasConnectedAccounts ? (
              <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={portfolioData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
                    <XAxis dataKey="date" stroke="hsl(220, 10%, 55%)" fontSize={12} />
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
                      labelStyle={{ color: "hsl(0, 0%, 95%)" }}
                      formatter={(value: number) => [`$${value.toLocaleString()}`, "Value"]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="hsl(142, 71%, 45%)"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorValue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <DataPlaceholder
                title="No Data Available"
                description="Connect an account to view your portfolio performance over time"
                className="h-[180px]"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Recent Trades & Previous Trades */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Trades */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Recent Trades
              </CardTitle>
              <Link to="/breakdown">
                <Button variant="ghost" size="sm">
                  View All <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : recentTrades.length > 0 ? (
                <div className="space-y-3">
                  {recentTrades.map((trade) => (
                    <div
                      key={trade.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={trade.type === "BUY" ? "default" : "secondary"}
                          className={trade.type === "BUY" ? "bg-primary" : "bg-destructive"}
                        >
                          {trade.type}
                        </Badge>
                        <div>
                          <p className="font-mono font-bold">{trade.symbol}</p>
                          <p className="text-sm text-muted-foreground">
                            {trade.shares} shares @ ${trade.price}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">{trade.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataPlaceholder
                  title="No Trades Yet"
                  description="Connect a brokerage account to see your trades"
                  className="min-h-[200px]"
                />
              )}
            </CardContent>
          </Card>

          {/* Trading Strategies */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                Trading Strategies
              </CardTitle>
              <Link to="/strategizer">
                <Button variant="ghost" size="sm">
                  Manage <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {displayStrategies.length > 0 ? (
                <div className="space-y-3">
                  {displayStrategies.map((strategy) => (
                    <div
                      key={strategy.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${strategy.status === "active" ? "bg-primary" : "bg-muted-foreground"}`} />
                        <div>
                          <p className="font-medium">{strategy.name}</p>
                          <p className="text-sm text-muted-foreground">{strategy.type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className={strategy.status === "active" ? "border-primary text-primary" : ""}>
                          {strategy.status}
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">{strategy.nextRun}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Zap className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No strategies configured</p>
                  <p className="text-sm">Create trading strategies to automate your investments</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Trade History */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="h-5 w-5 text-muted-foreground" />
                Trade History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[200px] w-full" />
              ) : previousTrades.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left py-2 px-3 text-sm font-medium text-muted-foreground">Date</th>
                        <th className="text-left py-2 px-3 text-sm font-medium text-muted-foreground">Symbol</th>
                        <th className="text-left py-2 px-3 text-sm font-medium text-muted-foreground">Type</th>
                        <th className="text-right py-2 px-3 text-sm font-medium text-muted-foreground">Amount</th>
                        <th className="text-right py-2 px-3 text-sm font-medium text-muted-foreground">P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previousTrades.map((trade, idx) => (
                        <tr key={idx} className="border-b border-border/50 hover:bg-secondary/30">
                          <td className="py-2 px-3 text-sm">{trade.date}</td>
                          <td className="py-2 px-3 font-mono font-bold text-primary">{trade.symbol}</td>
                          <td className="py-2 px-3">
                            <Badge variant="outline" className={trade.type === "BUY" ? "border-primary text-primary" : trade.type === "SELL" ? "border-destructive text-destructive" : ""}>
                              {trade.type}
                            </Badge>
                          </td>
                          <td className="py-2 px-3 text-right">${trade.amount.toLocaleString()}</td>
                          <td className={`py-2 px-3 text-right font-medium ${trade.pnl >= 0 ? "text-primary" : "text-destructive"}`}>
                            {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <DataPlaceholder
                  title="No Trade History"
                  description="Import transactions via CSV or connect a brokerage account"
                  className="min-h-[200px]"
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Notifications, Chatbot */}
        <div className="space-y-6">
          {/* Notifications */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                Notifications
              </CardTitle>
              <Link to="/notifications">
                <Button variant="ghost" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-4">
              {notifications.length > 0 ? (
                <div className="space-y-2">
                  {notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`p-3 rounded-lg border transition-colors ${notif.read
                        ? "bg-secondary/30 border-border"
                        : "bg-primary/5 border-primary/30"
                        }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`p-1.5 rounded-full ${notif.read ? "bg-muted" : "bg-primary/20"}`}>
                          <BellRing className={`h-3 w-3 ${notif.read ? "text-muted-foreground" : "text-primary"}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{notif.title}</p>
                          <p className="text-xs text-muted-foreground">{notif.time}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4 text-muted-foreground">
                  <Bell className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No notifications yet</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Settings */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Quick Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Price Alerts</span>
                </div>
                <Switch
                  checked={notificationSettings.priceAlerts}
                  onCheckedChange={(checked) => updateNotificationSetting('priceAlerts', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Trade Alerts</span>
                </div>
                <Switch
                  checked={notificationSettings.tradeExecutions}
                  onCheckedChange={(checked) => updateNotificationSetting('tradeExecutions', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Goal Progress</span>
                </div>
                <Switch
                  checked={notificationSettings.goalProgress}
                  onCheckedChange={(checked) => updateNotificationSetting('goalProgress', checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* AI Chatbot Placeholder */}
          <Card className="border-2 border-dashed border-muted">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-muted-foreground" />
                AI Financial Advisor
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-6">
                <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
                <p className="text-sm text-muted-foreground mb-3">
                  Ask questions about your finances
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Ask anything..."
                    className="flex-1 px-3 py-2 text-sm rounded-lg bg-secondary border border-border focus:outline-none focus:ring-2 focus:ring-primary"
                    disabled
                  />
                  <Button size="sm" disabled>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2">Coming soon</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
