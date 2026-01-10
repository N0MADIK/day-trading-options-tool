import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from '@/components/ui/dialog';
import { 
  Calculator, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  ChevronDown,
  ChevronRight,
  DollarSign,
  Percent,
  Info,
  Search,
  Loader2,
  Target,
  Zap,
  Send,
  BarChart3,
  Settings2,
  History,
} from 'lucide-react';
import { useConnections } from '@/hooks/useConnections';
import { useMarketDataConnections, MARKET_DATA_PROVIDERS } from '@/hooks/useMarketDataConnections';
import { useTaxCalculator, TradeAnalysis } from '@/hooks/useTaxCalculator';
import { OptionsChainViewer } from './OptionsChainViewer';
import { PositionSizingCalculator } from './PositionSizingCalculator';
import { OrderPreviewDialog } from './OrderPreviewDialog';
import { OrderManagement } from './OrderManagement';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { supabase } from '@/integrations/supabase/client';

interface TradeAnalyzerProps {
  onTradeAnalyzed?: (analysis: TradeAnalysis) => void;
}

type OrderType = 'market' | 'limit';
type TradeAction = 'buy' | 'sell';
type AssetType = 'stock' | 'option';

interface QuoteData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  bid: number;
  ask: number;
  bidSize?: number;
  askSize?: number;
  high: number;
  low: number;
  open?: number;
  volume: number;
  lastUpdated: string;
  provider: string;
}

export function TradeAnalyzer({ onTradeAnalyzed }: TradeAnalyzerProps) {
  const { holdings, transactions, accounts, loading } = useConnections();
  const { subscriptions, getActiveProvider, getCredentials } = useMarketDataConnections();
  const { analyzeTradeRequirements, getHoldingsSummary, taxRates } = useTaxCalculator(holdings, transactions);

  // Brokerage credentials state
  const [brokerageCredentials, setBrokerageCredentials] = useState<{ api_key: string; api_secret: string } | null>(null);

  const [tradeSymbol, setTradeSymbol] = useState('');
  const [tradeQuantity, setTradeQuantity] = useState('');
  const [tradePrice, setTradePrice] = useState('');
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [analysis, setAnalysis] = useState<TradeAnalysis | null>(null);
  const [expandedRecommendations, setExpandedRecommendations] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState('trade');

  // Trade settings
  const [orderType, setOrderType] = useState<OrderType>('limit');
  const [tradeAction, setTradeAction] = useState<TradeAction>('buy');
  const [assetType, setAssetType] = useState<AssetType>('stock');
  const [limitPrice, setLimitPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  
  // Quote data
  const [quote, setQuote] = useState<QuoteData | null>(null);
  const [fetchingQuote, setFetchingQuote] = useState(false);

  // Order execution
  const [showOrderPreview, setShowOrderPreview] = useState(false);

  const activeProvider = getActiveProvider();
  const providerInfo = activeProvider 
    ? MARKET_DATA_PROVIDERS.find(p => p.id === activeProvider.provider_name)
    : MARKET_DATA_PROVIDERS.find(p => p.id === 'yfinance');

  // Check if we have tradeable brokerage connection
  const hasBrokerageConnection = subscriptions.some(
    s => s.provider_name === 'alpaca' || s.provider_name === 'interactive-brokers'
  );
  const brokerageProvider = subscriptions.find(
    s => s.provider_name === 'alpaca' || s.provider_name === 'interactive-brokers'
  );

  // Fetch brokerage credentials on mount
  useEffect(() => {
    const fetchBrokerageCredentials = async () => {
      if (brokerageProvider?.provider_name) {
        const creds = await getCredentials(brokerageProvider.provider_name);
        if (creds && creds.api_key && creds.api_secret) {
          setBrokerageCredentials({
            api_key: creds.api_key,
            api_secret: creds.api_secret,
          });
        }
      }
    };
    fetchBrokerageCredentials();
  }, [brokerageProvider, getCredentials]);

  // Get credentials for API calls
  const getProviderCredentials = useCallback(() => {
    if (!activeProvider?.has_credentials) return undefined;
    return brokerageCredentials || undefined;
  }, [activeProvider, brokerageCredentials]);

  // Fetch real quote from edge function
  const fetchSymbolQuote = useCallback(async (symbol: string) => {
    if (!symbol || symbol.length < 1) {
      setQuote(null);
      return;
    }

    setFetchingQuote(true);
    try {
      const provider = activeProvider?.provider_name || 'yfinance';
      const credentials = getProviderCredentials();

      const { data, error } = await supabase.functions.invoke('market-data', {
        body: {
          action: 'quote',
          symbol,
          provider,
          credentials,
        },
      });

      if (error) throw error;
      if (data?.error) throw new Error(data.error);

      if (data?.quote) {
        setQuote(data.quote);
        // Auto-fill price if limit order
        if (orderType === 'limit' && !tradePrice) {
          setTradePrice(data.quote.price.toFixed(2));
          setLimitPrice(data.quote.price.toFixed(2));
        } else if (orderType === 'market') {
          setTradePrice(data.quote.price.toFixed(2));
        }
      }
    } catch (error: unknown) {
      console.error('Error fetching quote:', error);
      toast.error('Failed to fetch quote');
    } finally {
      setFetchingQuote(false);
    }
  }, [activeProvider, orderType, tradePrice, getProviderCredentials]);

  // Debounced symbol lookup
  useEffect(() => {
    const timer = setTimeout(() => {
      if (tradeSymbol.length >= 1) {
        fetchSymbolQuote(tradeSymbol);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [tradeSymbol, fetchSymbolQuote]);

  // Update trade price when order type changes
  useEffect(() => {
    if (quote) {
      if (orderType === 'market') {
        setTradePrice(quote.price.toFixed(2));
      } else if (limitPrice) {
        setTradePrice(limitPrice);
      }
    }
  }, [orderType, quote, limitPrice]);

  // Calculate available cash from selected account
  const availableCash = selectedAccount && selectedAccount !== 'all'
    ? accounts.find(a => a.id === selectedAccount)?.balance || 0
    : accounts.reduce((sum, a) => {
        if (a.institution_type === 'bank') {
          return sum + (a.balance || 0);
        }
        return sum;
      }, 0);

  const tradeCost = parseFloat(tradeQuantity || '0') * parseFloat(tradePrice || '0');

  const handleAnalyze = () => {
    if (tradeCost <= 0) return;

    const result = analyzeTradeRequirements(tradeCost, availableCash);
    setAnalysis(result);
    onTradeAnalyzed?.(result);
  };

  const toggleRecommendation = (holdingId: string) => {
    setExpandedRecommendations(prev => {
      const next = new Set(prev);
      if (next.has(holdingId)) {
        next.delete(holdingId);
      } else {
        next.add(holdingId);
      }
      return next;
    });
  };

  const handleOptionSelected = (option: any) => {
    setTradePrice(option.lastPrice.toFixed(2));
    setLimitPrice(option.ask.toFixed(2));
    toast.success(`Selected ${option.type.toUpperCase()} at strike ${option.strike}`);
  };

  const handleQuantityFromSizing = (qty: number) => {
    setTradeQuantity(qty.toString());
    setActiveTab('trade');
    toast.success(`Applied position size: ${qty} shares`);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value / 100);
  };

  const holdingsSummary = getHoldingsSummary();

  if (loading) {
    return (
      <Card className="border-border bg-card">
        <CardContent className="p-6 text-center text-muted-foreground">
          Loading portfolio data...
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Market Data Provider Info */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border">
        <div className="flex items-center gap-2">
          <span className="text-lg">{providerInfo?.logo || '📈'}</span>
          <div>
            <p className="text-sm font-medium text-foreground">{providerInfo?.name || 'Yahoo Finance'}</p>
            <p className="text-xs text-muted-foreground">Market Data Provider</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {quote && (
            <span className="text-muted-foreground">
              Last updated: {format(new Date(quote.lastUpdated), 'HH:mm:ss')}
            </span>
          )}
          {hasBrokerageConnection && (
            <Badge variant="default" className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              Trading Enabled
            </Badge>
          )}
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="trade" className="flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Trade Setup
          </TabsTrigger>
          <TabsTrigger value="sizing" className="flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            Position Sizing
          </TabsTrigger>
          <TabsTrigger value="options" className="flex items-center gap-2" disabled={assetType !== 'option'}>
            <BarChart3 className="h-4 w-4" />
            Options Chain
          </TabsTrigger>
          <TabsTrigger value="orders" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Orders
          </TabsTrigger>
          <TabsTrigger value="holdings" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Holdings
          </TabsTrigger>
        </TabsList>

        {/* Trade Setup Tab */}
        <TabsContent value="trade" className="space-y-6">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Trade Analyzer
              </CardTitle>
              <CardDescription>
                Set up your trade parameters and analyze funding requirements with tax implications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Trade Type Selection */}
              <div className="flex gap-6">
                <div className="space-y-2">
                  <Label>Action</Label>
                  <RadioGroup value={tradeAction} onValueChange={(v) => setTradeAction(v as TradeAction)} className="flex gap-4">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="buy" id="buy" />
                      <Label htmlFor="buy" className="cursor-pointer text-primary font-medium">Buy</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="sell" id="sell" />
                      <Label htmlFor="sell" className="cursor-pointer text-destructive font-medium">Sell</Label>
                    </div>
                  </RadioGroup>
                </div>
                <div className="space-y-2">
                  <Label>Asset Type</Label>
                  <RadioGroup value={assetType} onValueChange={(v) => setAssetType(v as AssetType)} className="flex gap-4">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="stock" id="stock" />
                      <Label htmlFor="stock" className="cursor-pointer">Stock/ETF</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="option" id="option" />
                      <Label htmlFor="option" className="cursor-pointer">Option</Label>
                    </div>
                  </RadioGroup>
                </div>
              </div>

              {/* Symbol and Quote */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Symbol</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="e.g., AAPL"
                      value={tradeSymbol}
                      onChange={(e) => setTradeSymbol(e.target.value.toUpperCase())}
                      className="pl-10"
                    />
                    {fetchingQuote && (
                      <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                    )}
                  </div>
                </div>
                
                {/* Quote Display */}
                {quote && (
                  <div className="p-3 rounded-lg bg-secondary/50 border border-border">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-lg font-bold text-foreground">{quote.symbol}</p>
                          <Badge variant="outline" className="text-xs">{quote.provider}</Badge>
                        </div>
                        <p className="text-2xl font-bold text-foreground">{formatCurrency(quote.price)}</p>
                      </div>
                      <div className="text-right">
                        <div className={`flex items-center gap-1 ${quote.change >= 0 ? 'text-primary' : 'text-destructive'}`}>
                          {quote.change >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          <span className="font-medium">{quote.change >= 0 ? '+' : ''}{formatCurrency(quote.change)}</span>
                          <span>({quote.changePercent >= 0 ? '+' : ''}{quote.changePercent.toFixed(2)}%)</span>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          Bid: {formatCurrency(quote.bid)} / Ask: {formatCurrency(quote.ask)}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                      <span>H: {formatCurrency(quote.high)}</span>
                      <span>L: {formatCurrency(quote.low)}</span>
                      <span>Vol: {quote.volume.toLocaleString()}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Order Type and Price */}
              <div className="grid gap-4 md:grid-cols-4">
                <div className="space-y-2">
                  <Label>Order Type</Label>
                  <Select value={orderType} onValueChange={(v) => setOrderType(v as OrderType)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="market">
                        <div className="flex items-center gap-2">
                          <Zap className="h-4 w-4" />
                          Market
                        </div>
                      </SelectItem>
                      <SelectItem value="limit">
                        <div className="flex items-center gap-2">
                          <Target className="h-4 w-4" />
                          Limit
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Quantity {assetType === 'option' ? '(Contracts)' : '(Shares)'}</Label>
                  <Input
                    type="number"
                    placeholder={assetType === 'option' ? '10' : '100'}
                    value={tradeQuantity}
                    onChange={(e) => setTradeQuantity(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>
                    {orderType === 'market' ? 'Est. Price' : 'Limit Price'} 
                    {assetType === 'option' && ' (per contract)'}
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder={quote ? quote.price.toFixed(2) : '150.00'}
                    value={orderType === 'market' ? tradePrice : limitPrice}
                    onChange={(e) => {
                      if (orderType === 'limit') {
                        setLimitPrice(e.target.value);
                        setTradePrice(e.target.value);
                      }
                    }}
                    disabled={orderType === 'market'}
                    className={orderType === 'market' ? 'bg-muted' : ''}
                  />
                </div>
                <div className="space-y-2">
                  <Label>From Account</Label>
                  <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                    <SelectTrigger>
                      <SelectValue placeholder="All accounts" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All accounts</SelectItem>
                      {accounts.map((account) => (
                        <SelectItem key={account.id} value={account.id}>
                          {account.institution_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* P/L Limits */}
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <TrendingDown className="h-4 w-4 text-destructive" />
                    Stop Loss (Optional)
                  </Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      step="0.01"
                      placeholder={quote ? (quote.price * 0.95).toFixed(2) : 'Price'}
                      value={stopLoss}
                      onChange={(e) => setStopLoss(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {stopLoss && quote && (
                    <p className="text-xs text-destructive">
                      {((parseFloat(stopLoss) - quote.price) / quote.price * 100).toFixed(1)}% from current
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    Take Profit (Optional)
                  </Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      step="0.01"
                      placeholder={quote ? (quote.price * 1.1).toFixed(2) : 'Price'}
                      value={takeProfit}
                      onChange={(e) => setTakeProfit(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {takeProfit && quote && (
                    <p className="text-xs text-primary">
                      +{((parseFloat(takeProfit) - quote.price) / quote.price * 100).toFixed(1)}% from current
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Risk/Reward Ratio</Label>
                  <div className="p-2 rounded-lg bg-secondary/50 h-[40px] flex items-center">
                    {stopLoss && takeProfit && quote ? (
                      <span className="font-medium">
                        1 : {((parseFloat(takeProfit) - quote.price) / (quote.price - parseFloat(stopLoss))).toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground text-sm">Set stop loss & take profit</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Trade Summary */}
              <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 border border-border">
                <div>
                  <p className="text-sm text-muted-foreground">Trade Cost</p>
                  <p className="text-2xl font-bold text-foreground">
                    {formatCurrency(tradeCost * (assetType === 'option' ? 100 : 1))}
                  </p>
                  {assetType === 'option' && (
                    <p className="text-xs text-muted-foreground">
                      {tradeQuantity || 0} contracts × {formatCurrency(parseFloat(tradePrice || '0'))} × 100
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Available Cash</p>
                  <p className="text-2xl font-bold text-foreground">{formatCurrency(availableCash)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {tradeAction === 'buy' ? 'Shortfall' : 'Proceeds'}
                  </p>
                  {tradeAction === 'buy' ? (
                    <p className={`text-2xl font-bold ${tradeCost > availableCash ? 'text-destructive' : 'text-primary'}`}>
                      {tradeCost > availableCash ? formatCurrency(tradeCost - availableCash) : formatCurrency(0)}
                    </p>
                  ) : (
                    <p className="text-2xl font-bold text-primary">
                      {formatCurrency(tradeCost * (assetType === 'option' ? 100 : 1))}
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  <Button 
                    onClick={handleAnalyze} 
                    disabled={tradeCost <= 0 || tradeAction === 'sell'}
                    variant="outline"
                    className="min-w-[140px]"
                  >
                    Analyze Trade
                  </Button>
                  {hasBrokerageConnection && (
                    <Dialog open={showOrderPreview} onOpenChange={setShowOrderPreview}>
                      <DialogTrigger asChild>
                        <Button 
                          disabled={tradeCost <= 0 || !tradeQuantity}
                          className="min-w-[140px]"
                        >
                          <Send className="h-4 w-4 mr-2" />
                          Preview Order
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-lg">
                        <OrderPreviewDialog
                          symbol={tradeSymbol}
                          quantity={parseInt(tradeQuantity || '0')}
                          side={tradeAction}
                          orderType={orderType}
                          limitPrice={parseFloat(limitPrice) || undefined}
                          stopLoss={parseFloat(stopLoss) || undefined}
                          takeProfit={parseFloat(takeProfit) || undefined}
                          credentials={brokerageCredentials || { api_key: '', api_secret: '' }}
                          broker={brokerageProvider?.provider_name === 'alpaca' ? 'alpaca' : 'interactive_brokers'}
                          onOrderSubmitted={() => {
                            setShowOrderPreview(false);
                            toast.success('Order submitted!');
                          }}
                          onClose={() => setShowOrderPreview(false)}
                        />
                      </DialogContent>
                    </Dialog>
                  )}
                  {!hasBrokerageConnection && (
                    <p className="text-xs text-muted-foreground text-center">
                      Connect Alpaca or IB to trade
                    </p>
                  )}
                </div>
              </div>

              {/* P/L Projection */}
              {quote && tradeQuantity && (
                <div className="grid gap-4 md:grid-cols-3">
                  <Card className="border-border bg-card">
                    <CardContent className="p-4">
                      <p className="text-sm text-muted-foreground mb-1">If hits Stop Loss</p>
                      <p className="text-xl font-bold text-destructive">
                        {stopLoss ? formatCurrency((parseFloat(stopLoss) - parseFloat(tradePrice || '0')) * parseFloat(tradeQuantity) * (assetType === 'option' ? 100 : 1)) : '—'}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="border-border bg-card">
                    <CardContent className="p-4">
                      <p className="text-sm text-muted-foreground mb-1">Breakeven Price</p>
                      <p className="text-xl font-bold text-foreground">
                        {formatCurrency(parseFloat(tradePrice || '0'))}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="border-border bg-card">
                    <CardContent className="p-4">
                      <p className="text-sm text-muted-foreground mb-1">If hits Take Profit</p>
                      <p className="text-xl font-bold text-primary">
                        {takeProfit ? formatCurrency((parseFloat(takeProfit) - parseFloat(tradePrice || '0')) * parseFloat(tradeQuantity) * (assetType === 'option' ? 100 : 1)) : '—'}
                      </p>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Analysis Results */}
          {analysis && (
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {analysis.canAffordTrade ? (
                    <CheckCircle className="h-5 w-5 text-primary" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-destructive" />
                  )}
                  Trade Analysis Results
                </CardTitle>
                <CardDescription>
                  {analysis.canAffordTrade
                    ? 'You can fund this trade with the following sales'
                    : 'Insufficient funds to complete this trade'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="p-4 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                      <DollarSign className="h-4 w-4" />
                      Need to Sell
                    </div>
                    <p className="text-xl font-bold text-foreground">{formatCurrency(analysis.totalProceeds)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                      <Percent className="h-4 w-4" />
                      Estimated Tax
                    </div>
                    <p className="text-xl font-bold text-destructive">{formatCurrency(analysis.totalTax)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                      <TrendingUp className="h-4 w-4" />
                      Net After Tax
                    </div>
                    <p className="text-xl font-bold text-primary">{formatCurrency(analysis.netAfterTax)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                      <Info className="h-4 w-4" />
                      Tax Rates
                    </div>
                    <p className="text-sm text-foreground">
                      Short: {formatPercent(taxRates.shortTerm * 100)} / Long: {formatPercent(taxRates.longTerm * 100)}
                    </p>
                  </div>
                </div>

                {/* Recommendations */}
                {analysis.recommendations.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-semibold mb-4">Recommended Sales</h4>
                      <div className="space-y-3">
                        {analysis.recommendations.map((rec) => (
                          <Collapsible
                            key={rec.holding.id}
                            open={expandedRecommendations.has(rec.holding.id)}
                            onOpenChange={() => toggleRecommendation(rec.holding.id)}
                          >
                            <div className="border border-border rounded-lg overflow-hidden">
                              <CollapsibleTrigger asChild>
                                <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-secondary/50 transition-colors">
                                  <div className="flex items-center gap-4">
                                    {expandedRecommendations.has(rec.holding.id) ? (
                                      <ChevronDown className="h-4 w-4" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4" />
                                    )}
                                    <div>
                                      <div className="flex items-center gap-2">
                                        <span className="font-semibold">{rec.holding.symbol}</span>
                                        <Badge variant={rec.isLongTerm ? 'default' : 'secondary'}>
                                          {rec.isLongTerm ? 'Long-term' : 'Short-term'}
                                        </Badge>
                                      </div>
                                      <p className="text-sm text-muted-foreground">{rec.holding.name}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-8 text-right">
                                    <div>
                                      <p className="text-sm text-muted-foreground">Sell</p>
                                      <p className="font-medium">{rec.quantityToSell.toFixed(2)} shares</p>
                                    </div>
                                    <div>
                                      <p className="text-sm text-muted-foreground">Proceeds</p>
                                      <p className="font-medium">{formatCurrency(rec.totalProceeds)}</p>
                                    </div>
                                    <div>
                                      <p className="text-sm text-muted-foreground">Tax</p>
                                      <p className={`font-medium ${rec.estimatedTax > 0 ? 'text-destructive' : 'text-primary'}`}>
                                        {formatCurrency(rec.estimatedTax)}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-sm text-muted-foreground">Net</p>
                                      <p className="font-medium text-primary">{formatCurrency(rec.netProceeds)}</p>
                                    </div>
                                  </div>
                                </div>
                              </CollapsibleTrigger>
                              <CollapsibleContent>
                                <div className="border-t border-border p-4 bg-secondary/20">
                                  <h5 className="text-sm font-medium mb-3">Tax Lots</h5>
                                  <Table>
                                    <TableHeader>
                                      <TableRow>
                                        <TableHead>Purchase Date</TableHead>
                                        <TableHead>Quantity</TableHead>
                                        <TableHead>Cost Basis</TableHead>
                                        <TableHead>Current Price</TableHead>
                                        <TableHead>Gain/Loss</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Tax Rate</TableHead>
                                        <TableHead>Est. Tax</TableHead>
                                      </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                      {rec.taxLots.map((lot, idx) => (
                                        <TableRow key={idx}>
                                          <TableCell>{format(lot.purchaseDate, 'MMM d, yyyy')}</TableCell>
                                          <TableCell>{lot.quantity.toFixed(2)}</TableCell>
                                          <TableCell>{formatCurrency(lot.purchasePrice)}</TableCell>
                                          <TableCell>{formatCurrency(lot.currentPrice)}</TableCell>
                                          <TableCell>
                                            <span className={lot.gain >= 0 ? 'text-primary' : 'text-destructive'}>
                                              {formatCurrency(lot.gain)} ({formatPercent(lot.gainPercent)})
                                            </span>
                                          </TableCell>
                                          <TableCell>
                                            <Badge variant={lot.isLongTerm ? 'default' : 'secondary'} className="text-xs">
                                              {lot.isLongTerm ? 'Long' : 'Short'}
                                            </Badge>
                                          </TableCell>
                                          <TableCell>{formatPercent(lot.taxRate * 100)}</TableCell>
                                          <TableCell className={lot.estimatedTax > 0 ? 'text-destructive' : ''}>
                                            {formatCurrency(lot.estimatedTax)}
                                          </TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </div>
                              </CollapsibleContent>
                            </div>
                          </Collapsible>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Position Sizing Tab */}
        <TabsContent value="sizing">
          <PositionSizingCalculator
            accountBalance={availableCash}
            currentPrice={quote?.price || parseFloat(tradePrice) || 100}
            symbol={tradeSymbol}
            stopLossPrice={parseFloat(stopLoss) || undefined}
            onQuantityChange={handleQuantityFromSizing}
          />
        </TabsContent>

        {/* Options Chain Tab */}
        <TabsContent value="options">
          {tradeSymbol ? (
            <OptionsChainViewer
              symbol={tradeSymbol}
              provider={activeProvider?.provider_name || 'yfinance'}
              credentials={getProviderCredentials()}
              underlyingPrice={quote?.price}
              onSelectOption={handleOptionSelected}
            />
          ) : (
            <Card className="border-border bg-card">
              <CardContent className="p-6 text-center text-muted-foreground">
                Enter a symbol in the Trade Setup tab to view options chain
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders">
          <OrderManagement
            credentials={brokerageCredentials || { api_key: '', api_secret: '' }}
            paperTrading={true}
            onRefresh={() => {}}
          />
        </TabsContent>

        {/* Holdings Tab */}
        <TabsContent value="holdings">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Your Holdings & Tax Positions
              </CardTitle>
              <CardDescription>
                Current holdings with unrealized gains/losses and tax implications
              </CardDescription>
            </CardHeader>
            <CardContent>
              {holdingsSummary.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No holdings found. Connect an account to see your portfolio.
                </p>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Symbol</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead>Market Value</TableHead>
                        <TableHead>Unrealized Gain</TableHead>
                        <TableHead>Tax Type</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {holdingsSummary.map(({ holding, hasLongTermLots, hasShortTermLots }) => (
                        <TableRow key={holding.id}>
                          <TableCell className="font-medium">{holding.symbol}</TableCell>
                          <TableCell className="text-muted-foreground">{holding.name}</TableCell>
                          <TableCell>{holding.quantity?.toFixed(2)}</TableCell>
                          <TableCell>{formatCurrency(holding.market_value || 0)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {(holding.unrealized_pnl || 0) >= 0 ? (
                                <TrendingUp className="h-4 w-4 text-primary" />
                              ) : (
                                <TrendingDown className="h-4 w-4 text-destructive" />
                              )}
                              <span className={(holding.unrealized_pnl || 0) >= 0 ? 'text-primary' : 'text-destructive'}>
                                {formatCurrency(holding.unrealized_pnl || 0)}
                                {holding.unrealized_pnl_percent && (
                                  <span className="text-sm ml-1">
                                    ({formatPercent(holding.unrealized_pnl_percent)})
                                  </span>
                                )}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {hasLongTermLots && (
                                <Badge variant="default" className="text-xs">Long</Badge>
                              )}
                              {hasShortTermLots && (
                                <Badge variant="secondary" className="text-xs">Short</Badge>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
