import { useState, useMemo, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  X,
  Search,
  TrendingUp,
  TrendingDown,
  Star,
  Bell,
  RefreshCw,
  Loader2,
  LineChart,
  StarOff,
  Target,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";
import { InteractiveChart, ChartDataPoint, IndicatorSeries } from "@/components/market/InteractiveChart";
import { IndicatorDialog, IndicatorConfig } from "@/components/market/IndicatorDialog";
import { PythonIndicatorIDE, CustomIndicatorScript } from "@/components/market/PythonIndicatorIDE";
import { TimeframeSelector, Timeframe } from "@/components/market/TimeframeSelector";
import { SignalDetector } from "@/components/market/SignalDetector";
import { RuleBacktester } from "@/components/strategizer/RuleBacktester";
import { Time } from "lightweight-charts";
import { useMarketDataConnections, MARKET_DATA_PROVIDERS } from "@/hooks/useMarketDataConnections";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

interface WatchlistItem {
  id?: string;
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  marketCap: string;
  high52w: number;
  low52w: number;
  notes?: string;
  price_alert_above?: number;
  price_alert_below?: number;
}

// Generate realistic-looking mock data for any ticker
const generateCandlestickData = (basePrice: number, days: number = 90): ChartDataPoint[] => {
  const data: ChartDataPoint[] = [];
  let price = basePrice * 0.9;
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const timestamp = Math.floor(date.getTime() / 1000) as Time;

    const volatility = basePrice * 0.02;
    const open = price;
    const change = (Math.random() - 0.48) * volatility;
    const close = Math.max(open + change, basePrice * 0.5);
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    const volume = Math.floor(Math.random() * 10000000) + 1000000;

    data.push({ time: timestamp, open, high, low, close, volume });
    price = close;
  }
  return data;
};

const generateOptionsChain = (currentPrice: number) => {
  const strikes = [];
  const baseStrike = Math.floor(currentPrice / 5) * 5;
  for (let i = -5; i <= 5; i++) {
    const strike = baseStrike + i * 5;
    const itm = strike < currentPrice;
    strikes.push({
      strike,
      callBid: parseFloat((Math.random() * 10 + (itm ? currentPrice - strike : 0.5)).toFixed(2)),
      callAsk: parseFloat((Math.random() * 10 + (itm ? currentPrice - strike : 0.7)).toFixed(2)),
      callVolume: Math.floor(Math.random() * 5000),
      callOI: Math.floor(Math.random() * 10000),
      putBid: parseFloat((Math.random() * 10 + (!itm ? strike - currentPrice : 0.5)).toFixed(2)),
      putAsk: parseFloat((Math.random() * 10 + (!itm ? strike - currentPrice : 0.7)).toFixed(2)),
      putVolume: Math.floor(Math.random() * 5000),
      putOI: Math.floor(Math.random() * 10000),
      itm,
    });
  }
  return strikes;
};

// Generate mock stock data for any symbol
const generateStockData = (symbol: string): WatchlistItem => {
  const basePrice = Math.random() * 500 + 10;
  const change = (Math.random() - 0.5) * basePrice * 0.05;
  const volume = Math.floor(Math.random() * 50) + 1;
  const marketCap = Math.floor(Math.random() * 2000) + 10;

  return {
    symbol: symbol.toUpperCase(),
    name: `${symbol.toUpperCase()} Corporation`,
    price: parseFloat(basePrice.toFixed(2)),
    change: parseFloat(change.toFixed(2)),
    changePercent: parseFloat(((change / basePrice) * 100).toFixed(2)),
    volume: `${volume.toFixed(1)}M`,
    marketCap: marketCap > 1000 ? `${(marketCap / 1000).toFixed(2)}T` : `${marketCap.toFixed(0)}B`,
    high52w: parseFloat((basePrice * 1.3).toFixed(2)),
    low52w: parseFloat((basePrice * 0.7).toFixed(2)),
  };
};

// Popular stock suggestions for search
const popularStocks = [
  "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "AMD", "NFLX", "DIS",
  "BA", "JPM", "V", "WMT", "PG", "JNJ", "UNH", "HD", "MA", "PFE",
  "SPY", "QQQ", "IWM", "VTI", "VOO", "VNQ", "GLD", "SLV", "TLT", "BND"
];

const calculateSMA = (data: ChartDataPoint[], period: number): IndicatorSeries => {
  const result: IndicatorSeries["data"] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;
    const sum = data.slice(i - period + 1, i + 1).reduce((acc, d) => acc + d.close, 0);
    result.push({ time: data[i].time, value: sum / period });
  }
  return { name: `SMA(${period})`, type: "line", data: result, color: "#3b82f6" };
};

const calculateEMA = (data: ChartDataPoint[], period: number): IndicatorSeries => {
  const result: IndicatorSeries["data"] = [];
  const multiplier = 2 / (period + 1);
  let ema = data.slice(0, period).reduce((acc, d) => acc + d.close, 0) / period;

  for (let i = period - 1; i < data.length; i++) {
    if (i === period - 1) {
      result.push({ time: data[i].time, value: ema });
    } else {
      ema = (data[i].close - ema) * multiplier + ema;
      result.push({ time: data[i].time, value: ema });
    }
  }
  return { name: `EMA(${period})`, type: "line", data: result, color: "#8b5cf6" };
};

export default function MarketScanner() {
  const { user } = useAuth();
  const { subscriptions, getActiveProvider } = useMarketDataConnections();

  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [selectedStock, setSelectedStock] = useState<WatchlistItem | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [optionsChain, setOptionsChain] = useState<ReturnType<typeof generateOptionsChain>>([]);
  const [timeframe, setTimeframe] = useState<Timeframe>("1D");
  const [activeIndicators, setActiveIndicators] = useState<IndicatorConfig[]>([]);
  const [customScripts, setCustomScripts] = useState<CustomIndicatorScript[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingToWatchlist, setSavingToWatchlist] = useState(false);
  const [showBacktester, setShowBacktester] = useState(false);
  const [backtestRule, setBacktestRule] = useState<any>(null);

  // Get active data provider
  const activeProvider = getActiveProvider();
  const providerInfo = MARKET_DATA_PROVIDERS.find(p => p.id === activeProvider?.provider_name) || MARKET_DATA_PROVIDERS[0];

  // Fetch user's watchlist from API
  const fetchWatchlist = useCallback(async () => {
    if (!user) return;

    try {
      const data = await api.get<Array<{
        id: string;
        symbol: string;
        name?: string;
        notes?: string;
        price_alert_above?: number;
        price_alert_below?: number;
      }>>('/watchlist');

      // Convert database records to WatchlistItem format with mock price data
      const items: WatchlistItem[] = (data || []).map(item => ({
        id: item.id,
        symbol: item.symbol,
        name: item.name || `${item.symbol} Corporation`,
        notes: item.notes || undefined,
        price_alert_above: item.price_alert_above || undefined,
        price_alert_below: item.price_alert_below || undefined,
        ...generateStockData(item.symbol),
      }));

      setWatchlist(items);

      // Select first item if none selected
      if (items.length > 0 && !selectedStock) {
        handleSelectStock(items[0]);
      }
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    }
  }, [user, selectedStock]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  // Search for stocks
  useEffect(() => {
    if (searchTerm.length === 0) {
      setSearchResults([]);
      return;
    }

    const term = searchTerm.toUpperCase();
    const matches = popularStocks.filter(s =>
      s.includes(term) || term.includes(s.slice(0, 2))
    ).slice(0, 8);

    // Always include the exact search term if it's valid (1-5 chars)
    if (term.length >= 1 && term.length <= 5 && !matches.includes(term)) {
      matches.unshift(term);
    }

    setSearchResults(matches);
  }, [searchTerm]);

  const indicatorSeries = useMemo(() => {
    const series: IndicatorSeries[] = [];
    activeIndicators.filter(i => i.enabled).forEach((ind) => {
      if (ind.type === "sma") series.push({ ...calculateSMA(chartData, ind.params.period || 20), color: ind.color });
      if (ind.type === "ema") series.push({ ...calculateEMA(chartData, ind.params.period || 12), color: ind.color });
    });
    return series;
  }, [chartData, activeIndicators]);

  const handleSearchStock = async (symbol: string) => {
    setLoading(true);
    setSearchTerm("");
    setSearchResults([]);

    try {
      // Generate mock data for the searched stock
      const stockData = generateStockData(symbol);
      setSelectedStock(stockData);
      setChartData(generateCandlestickData(stockData.price));
      setOptionsChain(generateOptionsChain(stockData.price));

      toast.success(`Loaded ${symbol} using ${providerInfo.name}`);
    } catch (error: any) {
      toast.error(`Failed to load ${symbol}: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToWatchlist = async () => {
    if (!selectedStock || !user) {
      toast.error('Please sign in to save to watchlist');
      return;
    }

    // Check if already in watchlist
    if (watchlist.some(s => s.symbol === selectedStock.symbol)) {
      toast.error(`${selectedStock.symbol} is already in your watchlist`);
      return;
    }

    setSavingToWatchlist(true);

    try {
      await api.post('/watchlist', {
        symbol: selectedStock.symbol,
        name: selectedStock.name,
      });

      toast.success(`${selectedStock.symbol} added to watchlist`);
      await fetchWatchlist();
    } catch (error: any) {
      toast.error(`Failed to add: ${error.message}`);
    } finally {
      setSavingToWatchlist(false);
    }
  };

  const handleRemoveFromWatchlist = async (item: WatchlistItem) => {
    if (!item.id || !user) return;

    try {
      await api.delete(`/watchlist/${item.id}`);

      toast.success(`${item.symbol} removed from watchlist`);

      if (selectedStock?.symbol === item.symbol) {
        setSelectedStock(null);
      }

      await fetchWatchlist();
    } catch (error: any) {
      toast.error(`Failed to remove: ${error.message}`);
    }
  };

  const handleSelectStock = (stock: WatchlistItem) => {
    setSelectedStock(stock);
    setChartData(generateCandlestickData(stock.price));
    setOptionsChain(generateOptionsChain(stock.price));
  };

  const handleTimeframeChange = (tf: Timeframe) => {
    setTimeframe(tf);
    if (selectedStock) {
      const days = tf === "1m" ? 1 : tf === "5m" ? 5 : tf === "15m" ? 7 : tf === "30m" ? 14 : tf === "1h" ? 30 : tf === "4h" ? 60 : tf === "1D" ? 90 : tf === "1W" ? 180 : 365;
      setChartData(generateCandlestickData(selectedStock.price, days));
    }
  };

  const handleRunScript = (script: CustomIndicatorScript) => {
    toast.success(`Custom indicator "${script.name}" applied to chart`);
  };

  const isInWatchlist = selectedStock && watchlist.some(s => s.symbol === selectedStock.symbol);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Market Scanner</h1>
        <p className="text-muted-foreground">Interactive charts with technical indicators and P/L analysis</p>
      </div>

      {/* Data Provider Indicator */}
      <Card className="border-cyan-500/30 bg-cyan-500/5">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LineChart className="h-5 w-5 text-cyan-400" />
            <div>
              <p className="font-medium text-cyan-400">Data Provider</p>
              <p className="text-sm text-muted-foreground">
                {activeProvider ? `Using ${providerInfo.name}` : 'No provider connected - using demo data'}
              </p>
            </div>
          </div>
          <Badge variant="outline" className="border-cyan-500/30 text-cyan-400">
            {providerInfo.logo} {providerInfo.name}
          </Badge>
        </CardContent>
      </Card>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search any ticker (e.g., AAPL, TSLA, BTC-USD)"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === "Enter" && searchTerm && handleSearchStock(searchTerm)}
                  className="pl-10 font-mono"
                />
              </div>
              <Button onClick={() => searchTerm && handleSearchStock(searchTerm)} disabled={loading || !searchTerm}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
                Search
              </Button>
            </div>

            {/* Search Suggestions */}
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-popover border border-border rounded-lg shadow-lg z-50">
                {searchResults.map((symbol) => (
                  <button
                    key={symbol}
                    className="w-full px-4 py-2 text-left hover:bg-secondary flex items-center justify-between font-mono first:rounded-t-lg last:rounded-b-lg"
                    onClick={() => handleSearchStock(symbol)}
                  >
                    <span className="font-bold text-primary">{symbol}</span>
                    <span className="text-sm text-muted-foreground">Search</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Star className="h-5 w-5 text-primary" />
                Watchlist
                {user && <Badge variant="outline" className="ml-auto">{watchlist.length}</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {!user ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Star className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Sign in to save watchlist</p>
                </div>
              ) : watchlist.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Star className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No stocks in watchlist</p>
                  <p className="text-sm mt-1">Search and add stocks above</p>
                </div>
              ) : (
                watchlist.map((stock) => (
                  <div
                    key={stock.id || stock.symbol}
                    className={`p-3 rounded-lg cursor-pointer transition-all border ${selectedStock?.symbol === stock.symbol ? "border-primary bg-primary/10" : "border-border hover:border-primary/50"}`}
                    onClick={() => handleSelectStock(stock)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-bold text-primary">{stock.symbol}</span>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRemoveFromWatchlist(stock); }}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-semibold">${stock.price.toFixed(2)}</span>
                      <span className={`flex items-center text-sm ${stock.change >= 0 ? "text-primary" : "text-destructive"}`}>
                        {stock.change >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                        {stock.changePercent >= 0 ? "+" : ""}{stock.changePercent.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-3 space-y-6">
          {selectedStock ? (
            <>
              <Card>
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-2xl font-bold font-mono text-primary">{selectedStock.symbol}</h2>
                        <Badge variant="outline">{selectedStock.name}</Badge>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-4xl font-bold">${selectedStock.price.toFixed(2)}</span>
                        <div className={`flex items-center gap-1 ${selectedStock.change >= 0 ? "text-primary" : "text-destructive"}`}>
                          {selectedStock.change >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                          <span className="text-xl font-semibold">{selectedStock.change >= 0 ? "+" : ""}${selectedStock.change.toFixed(2)} ({selectedStock.changePercent.toFixed(2)}%)</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {user && (
                        <Button
                          variant={isInWatchlist ? "outline" : "default"}
                          size="sm"
                          onClick={isInWatchlist ? () => handleRemoveFromWatchlist(watchlist.find(s => s.symbol === selectedStock.symbol)!) : handleAddToWatchlist}
                          disabled={savingToWatchlist}
                        >
                          {savingToWatchlist ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : isInWatchlist ? (
                            <><StarOff className="h-4 w-4 mr-2" />Remove</>
                          ) : (
                            <><Star className="h-4 w-4 mr-2" />Save</>
                          )}
                        </Button>
                      )}
                      <Button variant="outline" size="sm"><Bell className="h-4 w-4 mr-2" />Alert</Button>
                      <Button variant="outline" size="sm" onClick={() => handleSelectStock(selectedStock)}><RefreshCw className="h-4 w-4 mr-2" />Refresh</Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-border">
                    <div><p className="text-sm text-muted-foreground">Volume</p><p className="text-lg font-semibold">{selectedStock.volume}</p></div>
                    <div><p className="text-sm text-muted-foreground">Market Cap</p><p className="text-lg font-semibold">{selectedStock.marketCap}</p></div>
                    <div><p className="text-sm text-muted-foreground">52W High</p><p className="text-lg font-semibold">${selectedStock.high52w.toFixed(2)}</p></div>
                    <div><p className="text-sm text-muted-foreground">52W Low</p><p className="text-lg font-semibold">${selectedStock.low52w.toFixed(2)}</p></div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <Tabs defaultValue="chart" className="w-full">
                  <CardHeader className="pb-0">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <TabsList className="grid w-full max-w-lg grid-cols-4">
                        <TabsTrigger value="chart">Chart</TabsTrigger>
                        <TabsTrigger value="signals" className="flex items-center gap-1">
                          <Target className="h-3 w-3" />
                          Signals
                        </TabsTrigger>
                        <TabsTrigger value="backtest" className="flex items-center gap-1">
                          <BarChart3 className="h-3 w-3" />
                          Backtest
                        </TabsTrigger>
                        <TabsTrigger value="options">Options</TabsTrigger>
                      </TabsList>
                      <div className="flex items-center gap-2">
                        <TimeframeSelector selected={timeframe} onSelect={handleTimeframeChange} />
                        <IndicatorDialog activeIndicators={activeIndicators} onIndicatorsChange={setActiveIndicators} />
                        <PythonIndicatorIDE scripts={customScripts} onScriptsChange={setCustomScripts} onRunScript={handleRunScript} />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <TabsContent value="chart" className="mt-0">
                      <InteractiveChart data={chartData} indicators={indicatorSeries} symbol={selectedStock.symbol} />
                    </TabsContent>

                    <TabsContent value="signals" className="mt-0">
                      <SignalDetector
                        symbol={selectedStock.symbol}
                        currentPrice={selectedStock.price}
                        chartData={chartData}
                        onSignalDetected={(signal) => {
                          toast.success(`${signal.signalType.toUpperCase()} signal: ${signal.ruleName}`);
                        }}
                      />
                    </TabsContent>

                    <TabsContent value="backtest" className="mt-0">
                      <RuleBacktester
                        rule={{
                          id: 'market-scanner-backtest',
                          name: `${selectedStock.symbol} Strategy`,
                          symbol: selectedStock.symbol,
                          conditions: [
                            {
                              id: 'default-1',
                              indicatorId: 'sma-50',
                              indicatorName: 'SMA (50)',
                              indicatorType: 'sma',
                              operator: 'crosses_above',
                              value: 0,
                            }
                          ],
                          conditionLogic: 'and',
                          action: 'buy',
                          quantity: 100,
                        }}
                      />
                    </TabsContent>

                    <TabsContent value="options" className="mt-0">
                      <div className="mb-4 flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">Expiration: Jan 19, 2024</p>
                        <Badge variant="outline">Weekly Options</Badge>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-border">
                              <th colSpan={4} className="py-2 px-2 text-center bg-primary/10 text-primary">CALLS</th>
                              <th className="py-2 px-4 text-center bg-secondary">Strike</th>
                              <th colSpan={4} className="py-2 px-2 text-center bg-destructive/10 text-destructive">PUTS</th>
                            </tr>
                            <tr className="border-b border-border text-muted-foreground">
                              <th className="py-2 px-2 text-right">Bid</th>
                              <th className="py-2 px-2 text-right">Ask</th>
                              <th className="py-2 px-2 text-right">Vol</th>
                              <th className="py-2 px-2 text-right">OI</th>
                              <th className="py-2 px-4 text-center"></th>
                              <th className="py-2 px-2 text-right">Bid</th>
                              <th className="py-2 px-2 text-right">Ask</th>
                              <th className="py-2 px-2 text-right">Vol</th>
                              <th className="py-2 px-2 text-right">OI</th>
                            </tr>
                          </thead>
                          <tbody>
                            {optionsChain.map((row, idx) => (
                              <tr key={idx} className={`border-b border-border/50 hover:bg-secondary/50 ${row.strike === Math.floor(selectedStock.price / 5) * 5 ? "bg-primary/5" : ""}`}>
                                <td className={`py-2 px-2 text-right font-mono ${row.itm ? "bg-primary/10" : ""}`}>{row.callBid.toFixed(2)}</td>
                                <td className={`py-2 px-2 text-right font-mono ${row.itm ? "bg-primary/10" : ""}`}>{row.callAsk.toFixed(2)}</td>
                                <td className={`py-2 px-2 text-right text-muted-foreground ${row.itm ? "bg-primary/10" : ""}`}>{row.callVolume.toLocaleString()}</td>
                                <td className={`py-2 px-2 text-right text-muted-foreground ${row.itm ? "bg-primary/10" : ""}`}>{row.callOI.toLocaleString()}</td>
                                <td className="py-2 px-4 text-center font-mono font-bold bg-secondary">${row.strike}</td>
                                <td className={`py-2 px-2 text-right font-mono ${!row.itm ? "bg-destructive/10" : ""}`}>{row.putBid.toFixed(2)}</td>
                                <td className={`py-2 px-2 text-right font-mono ${!row.itm ? "bg-destructive/10" : ""}`}>{row.putAsk.toFixed(2)}</td>
                                <td className={`py-2 px-2 text-right text-muted-foreground ${!row.itm ? "bg-destructive/10" : ""}`}>{row.putVolume.toLocaleString()}</td>
                                <td className={`py-2 px-2 text-right text-muted-foreground ${!row.itm ? "bg-destructive/10" : ""}`}>{row.putOI.toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </TabsContent>
                  </CardContent>
                </Tabs>
              </Card>
            </>
          ) : (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Search className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">Search for a Stock</h3>
                <p className="text-muted-foreground text-center max-w-md">
                  Enter any ticker symbol above to view interactive charts, technical indicators, and options data using {providerInfo.name}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
