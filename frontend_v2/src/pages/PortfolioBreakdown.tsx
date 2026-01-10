import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  TrendingDown,
  MessageSquare,
  Send,
  ArrowUpRight,
  ArrowDownRight,
  Briefcase,
  DollarSign,
  BarChart3,
  PieChartIcon,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { useAuth } from "@/hooks/useAuth";
import { useConnections } from "@/hooks/useConnections";
import { useMockData, MOCK_DATA } from "@/hooks/useMockData";
import { DataPlaceholder } from "@/components/ui/DataPlaceholder";

export default function PortfolioBreakdown() {
  const { user } = useAuth();
  const { holdings, totalNetWorth, loading } = useConnections();
  const { showMockData } = useMockData();
  const [chartType, setChartType] = useState<"pie" | "bar">("pie");

  // Use mock data if toggle is on
  const hasHoldings = showMockData || holdings.length > 0;

  // Normalize holdings data (mock uses snake_case, real uses snake_case too)
  const displayHoldings = showMockData 
    ? MOCK_DATA.holdings.map(h => ({
        symbol: h.symbol,
        name: h.name || h.symbol,
        quantity: h.quantity,
        currentPrice: h.current_price || 0,
        averageCost: 0,
        marketValue: h.market_value || 0,
        unrealizedPnl: h.unrealized_pnl || 0,
        unrealizedPnlPercent: h.unrealized_pnl_percent || 0,
        assetType: 'stock',
      }))
    : holdings.map(h => ({
        symbol: h.symbol,
        name: h.name || h.symbol,
        quantity: h.quantity,
        currentPrice: h.current_price || 0,
        averageCost: h.average_cost || 0,
        marketValue: h.market_value || 0,
        unrealizedPnl: h.unrealized_pnl || 0,
        unrealizedPnlPercent: h.unrealized_pnl_percent || 0,
        assetType: h.asset_type || 'stock',
      }));

  // Calculate portfolio metrics
  const totalMarketValue = displayHoldings.reduce((sum, h) => sum + (h.marketValue || 0), 0);
  const totalUnrealizedPnl = displayHoldings.reduce((sum, h) => sum + (h.unrealizedPnl || 0), 0);
  const avgPnlPercent = displayHoldings.length > 0
    ? displayHoldings.reduce((sum, h) => sum + (h.unrealizedPnlPercent || 0), 0) / displayHoldings.length
    : 0;

  // Sort holdings by P/L for top gains and losses
  const sortedByPnl = [...displayHoldings].sort((a, b) => (b.unrealizedPnl || 0) - (a.unrealizedPnl || 0));
  const topGainers = sortedByPnl.filter(h => (h.unrealizedPnl || 0) > 0).slice(0, 5);
  const topLosers = sortedByPnl.filter(h => (h.unrealizedPnl || 0) < 0).slice(-5).reverse();

  // Asset allocation data
  const assetAllocation = (() => {
    const typeMap: Record<string, { value: number; color: string }> = {
      stock: { value: 0, color: "hsl(142, 71%, 45%)" },
      etf: { value: 0, color: "hsl(173, 58%, 39%)" },
      crypto: { value: 0, color: "hsl(38, 92%, 50%)" },
      bond: { value: 0, color: "hsl(197, 37%, 24%)" },
      mutual_fund: { value: 0, color: "hsl(280, 60%, 50%)" },
      other: { value: 0, color: "hsl(220, 15%, 50%)" },
    };

    displayHoldings.forEach(h => {
      const type = h.assetType?.toLowerCase() || 'stock';
      if (typeMap[type]) {
        typeMap[type].value += h.marketValue || 0;
      } else {
        typeMap.other.value += h.marketValue || 0;
      }
    });

    return Object.entries(typeMap)
      .filter(([_, data]) => data.value > 0)
      .map(([name, data]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1).replace('_', ' '),
        value: data.value,
        color: data.color,
      }));
  })();

  // Performance over time (simulated based on current holdings)
  const performanceData = (() => {
    if (displayHoldings.length === 0) return [];
    
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const baseValue = totalMarketValue * 0.7;
    const growth = (totalMarketValue - baseValue) / 12;
    
    return months.map((month, idx) => ({
      month,
      value: Math.round(baseValue + (growth * idx) + (Math.random() - 0.3) * growth * 0.5),
    }));
  })();

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Briefcase className="h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold mb-2">Portfolio Breakdown</h2>
        <p className="text-muted-foreground mb-4">Sign in to view your investment portfolio</p>
        <Button onClick={() => window.location.href = '/auth'}>Sign In</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Portfolio Breakdown</h1>
        <p className="text-muted-foreground">
          Detailed view of your investment holdings and performance
        </p>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-2 border-primary/20 bg-gradient-to-br from-card to-primary/5">
          <CardContent className="p-6">
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-40" />
              </div>
            ) : hasHoldings ? (
              <>
                <p className="text-sm text-muted-foreground mb-1">Total Portfolio Value</p>
                <h2 className="text-2xl font-bold">
                  ${totalMarketValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </h2>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {displayHoldings.length} holdings
                  </Badge>
                </div>
              </>
            ) : (
              <DataPlaceholder
                title="No Holdings"
                description="Connect a brokerage account"
                className="min-h-[100px]"
              />
            )}
          </CardContent>
        </Card>

        <Card className={`border-2 ${totalUnrealizedPnl >= 0 ? 'border-primary/20' : 'border-destructive/20'}`}>
          <CardContent className="p-6">
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-40" />
              </div>
            ) : hasHoldings ? (
              <>
                <p className="text-sm text-muted-foreground mb-1">Total Unrealized P/L</p>
                <h2 className={`text-2xl font-bold ${totalUnrealizedPnl >= 0 ? 'text-primary' : 'text-destructive'}`}>
                  {totalUnrealizedPnl >= 0 ? '+' : ''}${totalUnrealizedPnl.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </h2>
                <div className="flex items-center gap-2 mt-2">
                  <Badge
                    variant="outline"
                    className={totalUnrealizedPnl >= 0 ? 'border-primary text-primary' : 'border-destructive text-destructive'}
                  >
                    {totalUnrealizedPnl >= 0 ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                    {avgPnlPercent >= 0 ? '+' : ''}{avgPnlPercent.toFixed(2)}%
                  </Badge>
                </div>
              </>
            ) : (
              <DataPlaceholder
                title="No P/L Data"
                description="Connect an account to see P/L"
                className="min-h-[100px]"
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-40" />
              </div>
            ) : hasHoldings ? (
              <>
                <p className="text-sm text-muted-foreground mb-1">Asset Types</p>
                <h2 className="text-2xl font-bold">{assetAllocation.length}</h2>
                <div className="flex flex-wrap gap-1 mt-2">
                  {assetAllocation.slice(0, 3).map((asset) => (
                    <Badge key={asset.name} variant="secondary" className="text-xs">
                      {asset.name}
                    </Badge>
                  ))}
                </div>
              </>
            ) : (
              <DataPlaceholder
                title="No Assets"
                description="Connect to see asset types"
                className="min-h-[100px]"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Performance Chart and Holdings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Portfolio Performance Chart */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Portfolio Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[250px] w-full" />
              ) : hasHoldings ? (
                <div className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceData}>
                      <defs>
                        <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
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
                        labelStyle={{ color: "hsl(0, 0%, 95%)" }}
                        formatter={(value: number) => [`$${value.toLocaleString()}`, "Value"]}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="hsl(142, 71%, 45%)"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorPortfolio)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <DataPlaceholder
                  title="No Performance Data"
                  description="Connect a brokerage account to see performance"
                  className="h-[250px]"
                />
              )}
            </CardContent>
          </Card>

          {/* Top Gains */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Top Gainers
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
                </div>
              ) : topGainers.length > 0 ? (
                <div className="space-y-3">
                  {topGainers.map((holding, idx) => (
                    <div
                      key={holding.symbol}
                      className="flex items-center justify-between p-3 rounded-lg bg-primary/5 border border-primary/20"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold text-primary">
                          {idx + 1}
                        </div>
                        <div>
                          <p className="font-mono font-bold">{holding.symbol}</p>
                          <p className="text-sm text-muted-foreground truncate max-w-[150px]">
                            {holding.name}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-primary">
                          +${(holding.unrealizedPnl || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </p>
                        <div className="flex items-center gap-1 text-primary text-sm">
                          <ArrowUpRight className="h-3 w-3" />
                          +{(holding.unrealizedPnlPercent || 0).toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataPlaceholder
                  title="No Gains"
                  description="No positions with gains yet"
                  className="min-h-[200px]"
                />
              )}
            </CardContent>
          </Card>

          {/* Top Losses */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-destructive" />
                Top Losers
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
                </div>
              ) : topLosers.length > 0 ? (
                <div className="space-y-3">
                  {topLosers.map((holding, idx) => (
                    <div
                      key={holding.symbol}
                      className="flex items-center justify-between p-3 rounded-lg bg-destructive/5 border border-destructive/20"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-destructive/20 flex items-center justify-center text-sm font-bold text-destructive">
                          {idx + 1}
                        </div>
                        <div>
                          <p className="font-mono font-bold">{holding.symbol}</p>
                          <p className="text-sm text-muted-foreground truncate max-w-[150px]">
                            {holding.name}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-destructive">
                          ${(holding.unrealizedPnl || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </p>
                        <div className="flex items-center gap-1 text-destructive text-sm">
                          <ArrowDownRight className="h-3 w-3" />
                          {(holding.unrealizedPnlPercent || 0).toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataPlaceholder
                  title="No Losses"
                  description="No positions with losses"
                  className="min-h-[200px]"
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Allocation and AI Advisor */}
        <div className="space-y-6">
          {/* Asset Allocation */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg">Asset Allocation</CardTitle>
              <Tabs value={chartType} onValueChange={(v) => setChartType(v as "pie" | "bar")}>
                <TabsList className="h-8">
                  <TabsTrigger value="pie" className="h-6 px-2">
                    <PieChartIcon className="h-4 w-4" />
                  </TabsTrigger>
                  <TabsTrigger value="bar" className="h-6 px-2">
                    <BarChart3 className="h-4 w-4" />
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[200px] w-full" />
              ) : assetAllocation.length > 0 ? (
                <div className="h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    {chartType === "pie" ? (
                      <PieChart>
                        <Pie
                          data={assetAllocation}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={80}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {assetAllocation.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(220, 18%, 10%)",
                            border: "1px solid hsl(220, 15%, 20%)",
                            borderRadius: "8px",
                          }}
                          formatter={(value: number) => [`$${value.toLocaleString()}`, "Value"]}
                        />
                      </PieChart>
                    ) : (
                      <BarChart data={assetAllocation} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
                        <XAxis type="number" stroke="hsl(220, 10%, 55%)" fontSize={10} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                        <YAxis type="category" dataKey="name" stroke="hsl(220, 10%, 55%)" fontSize={10} width={60} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(220, 18%, 10%)",
                            border: "1px solid hsl(220, 15%, 20%)",
                            borderRadius: "8px",
                          }}
                          formatter={(value: number) => [`$${value.toLocaleString()}`, "Value"]}
                        />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                          {assetAllocation.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    )}
                  </ResponsiveContainer>
                </div>
              ) : (
                <DataPlaceholder
                  title="No Allocation Data"
                  description="Connect a brokerage account"
                  className="h-[200px]"
                />
              )}

              {/* Legend */}
              {assetAllocation.length > 0 && (
                <div className="mt-4 space-y-2">
                  {assetAllocation.map((asset) => (
                    <div key={asset.name} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: asset.color }} />
                        <span>{asset.name}</span>
                      </div>
                      <span className="text-muted-foreground">
                        ${asset.value.toLocaleString()} ({((asset.value / totalMarketValue) * 100).toFixed(1)}%)
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* All Holdings */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-muted-foreground" />
                All Holdings
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                </div>
              ) : displayHoldings.length > 0 ? (
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {displayHoldings.map((holding) => (
                    <div
                      key={holding.symbol}
                      className="flex items-center justify-between p-2 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                    >
                      <div>
                        <p className="font-mono font-bold text-sm">{holding.symbol}</p>
                        <p className="text-xs text-muted-foreground">{holding.quantity} shares</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">${(holding.marketValue || 0).toLocaleString()}</p>
                        <p className={`text-xs ${(holding.unrealizedPnl || 0) >= 0 ? 'text-primary' : 'text-destructive'}`}>
                          {(holding.unrealizedPnl || 0) >= 0 ? '+' : ''}{(holding.unrealizedPnlPercent || 0).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataPlaceholder
                  title="No Holdings"
                  description="Connect a brokerage account"
                  className="min-h-[200px]"
                />
              )}
            </CardContent>
          </Card>

          {/* AI Financial Advisor Placeholder */}
          <Card className="border-2 border-dashed border-muted">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-muted-foreground" />
                AI Portfolio Advisor
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-6">
                <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
                <p className="text-sm text-muted-foreground mb-3">
                  Get AI-powered insights on your portfolio
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Ask about your holdings..."
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
