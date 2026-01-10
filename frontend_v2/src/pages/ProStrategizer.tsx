import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Brain,
  Plus,
  Play,
  Pause,
  Settings,
  Trash2,
  TrendingUp,
  Clock,
  Zap,
  Target,
  BarChart3,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Database,
  Link2,
  Calculator,
  Activity,
  Edit2,
} from "lucide-react";
import { useConnections } from "@/hooks/useConnections";
import { useMarketDataConnections } from "@/hooks/useMarketDataConnections";
import { TradeAnalyzer } from "@/components/strategizer/TradeAnalyzer";
import { IndicatorTradeRules, IndicatorConfig } from "@/components/strategizer/IndicatorTradeRules";
import { StrategyEditor, Strategy } from "@/components/strategizer/StrategyEditor";
import { RuleBacktester } from "@/components/strategizer/RuleBacktester";

// Extended strategy interface for UI
interface StrategyItem {
  id: string;
  name: string;
  description: string;
  strategyType: string;
  isActive: boolean;
  isAutomated: boolean;
  account: string;
  dataSubscription: string | null;
  lastExecuted: string | null;
  nextExecution: string | null;
  performance: string;
  strategy?: Strategy; // Full strategy data for editing
}

// Mock strategies - will be replaced with database strategies
const mockStrategies: StrategyItem[] = [
  {
    id: "1",
    name: "Tech Growth DCA",
    description: "Dollar cost averaging into tech ETFs weekly",
    strategyType: "dca",
    isActive: true,
    isAutomated: true,
    account: "Fidelity Brokerage",
    dataSubscription: "Alpha Vantage Pro",
    lastExecuted: "2024-01-02 09:30 AM",
    nextExecution: "2024-01-09 09:30 AM",
    performance: "+12.5%",
  },
  {
    id: "2",
    name: "Portfolio Rebalancer",
    description: "Quarterly rebalancing to maintain 60/40 allocation",
    strategyType: "rebalance",
    isActive: true,
    isAutomated: false,
    account: "Vanguard 401k",
    dataSubscription: null,
    lastExecuted: "2023-12-01 10:00 AM",
    nextExecution: "2024-03-01 10:00 AM",
    performance: "+8.2%",
  },
  {
    id: "3",
    name: "Trailing Stop Loss",
    description: "Protect gains with 10% trailing stops",
    strategyType: "trailing_stop",
    isActive: false,
    isAutomated: true,
    account: "TD Ameritrade",
    dataSubscription: "Polygon.io Realtime",
    lastExecuted: "2023-11-15 03:45 PM",
    nextExecution: null,
    performance: "-2.1%",
  },
];

const strategyTypes = [
  { value: "dca", label: "Dollar Cost Averaging", icon: RefreshCw },
  { value: "rebalance", label: "Portfolio Rebalancing", icon: BarChart3 },
  { value: "trailing_stop", label: "Trailing Stop Loss", icon: AlertTriangle },
  { value: "momentum", label: "Momentum Trading", icon: TrendingUp },
  { value: "mean_reversion", label: "Mean Reversion", icon: Target },
];

// Mock custom indicators from Market Scanner (in production, these would come from the database)
const mockCustomIndicators: IndicatorConfig[] = [
  { id: 'custom-rsi-divergence', name: 'RSI Divergence', type: 'custom', enabled: true, color: '#f97316', params: { period: 14 } },
  { id: 'custom-volume-spike', name: 'Volume Spike Detector', type: 'custom', enabled: true, color: '#22c55e', params: { threshold: 2.5 } },
  { id: 'custom-trend-strength', name: 'Trend Strength Index', type: 'custom', enabled: true, color: '#a855f7', params: { lookback: 20 } },
];

export default function ProStrategizer() {
  const { toast } = useToast();
  const { accounts, holdings, transactions } = useConnections();
  const { subscriptions } = useMarketDataConnections();
  
  const [strategies, setStrategies] = useState<StrategyItem[]>(mockStrategies);
  const [isNewStrategyOpen, setIsNewStrategyOpen] = useState(false);
  const [isDataSubOpen, setIsDataSubOpen] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [backtestingStrategy, setBacktestingStrategy] = useState<StrategyItem | null>(null);
  
  // New strategy form state
  const [newStrategy, setNewStrategy] = useState({
    name: "",
    description: "",
    strategyType: "",
    account: "",
    dataSubscription: "",
    isAutomated: false,
  });

  // New data subscription form state
  const [newDataSub, setNewDataSub] = useState({
    providerName: "",
    providerType: "delayed",
    apiKey: "",
    subscriptionTier: "",
  });

  const handleToggleStrategy = (id: string) => {
    setStrategies(strategies.map(s => 
      s.id === id ? { ...s, isActive: !s.isActive } : s
    ));
    const strategy = strategies.find(s => s.id === id);
    toast({
      title: strategy?.isActive ? "Strategy Paused" : "Strategy Activated",
      description: `${strategy?.name} has been ${strategy?.isActive ? "paused" : "activated"}.`,
    });
  };

  const handleCreateStrategy = () => {
    if (!newStrategy.name || !newStrategy.strategyType || !newStrategy.account) {
      toast({
        variant: "destructive",
        title: "Missing Information",
        description: "Please fill in all required fields.",
      });
      return;
    }

    toast({
      title: "Strategy Created",
      description: `${newStrategy.name} has been created successfully.`,
    });
    setIsNewStrategyOpen(false);
    setNewStrategy({
      name: "",
      description: "",
      strategyType: "",
      account: "",
      dataSubscription: "",
      isAutomated: false,
    });
  };

  const handleEditStrategy = (strategyItem: StrategyItem) => {
    // Create or use existing strategy data
    const strategyData: Strategy = strategyItem.strategy || {
      id: strategyItem.id,
      name: strategyItem.name,
      description: strategyItem.description,
      symbol: 'AAPL', // Default symbol
      strategyType: strategyItem.strategyType,
      indicators: [],
      entry: {
        enabled: true,
        conditions: [],
        conditionLogic: 'and',
        orderType: 'market',
        positionSize: 100,
        positionSizeType: 'shares',
      },
      exit: {
        enabled: true,
        conditions: [],
        conditionLogic: 'or',
        takeProfitPercent: 10,
        stopLossPercent: 5,
      },
      isActive: strategyItem.isActive,
      isAutomated: strategyItem.isAutomated,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setEditingStrategy(strategyData);
  };

  const handleSaveStrategy = (strategy: Strategy) => {
    setStrategies(prev => prev.map(s => 
      s.id === strategy.id 
        ? { 
            ...s, 
            name: strategy.name,
            description: strategy.description,
            strategyType: strategy.strategyType,
            isAutomated: strategy.isAutomated,
            isActive: strategy.isActive,
            strategy: strategy,
          }
        : s
    ));
    setEditingStrategy(null);
    toast({
      title: "Strategy Updated",
      description: `${strategy.name} has been saved successfully.`,
    });
  };

  const handleDeleteStrategy = (id: string) => {
    setStrategies(prev => prev.filter(s => s.id !== id));
    toast({
      title: "Strategy Deleted",
      description: "The strategy has been removed.",
    });
  };

  const getBacktestRule = (strategy: StrategyItem) => ({
    id: strategy.id,
    name: strategy.name,
    symbol: strategy.strategy?.symbol || 'AAPL',
    conditions: strategy.strategy?.entry.conditions.map(c => ({
      id: c.id,
      indicatorId: c.indicatorId,
      indicatorName: c.indicatorName,
      indicatorType: 'sma',
      operator: c.operator,
      value: c.value,
      secondaryValue: c.secondaryValue,
    })) || [],
    conditionLogic: strategy.strategy?.entry.conditionLogic || 'and',
    action: 'buy' as const,
    quantity: strategy.strategy?.entry.positionSize || 100,
  });

  const handleAddDataSubscription = () => {
    if (!newDataSub.providerName || !newDataSub.apiKey) {
      toast({
        variant: "destructive",
        title: "Missing Information",
        description: "Please provide the provider name and API key.",
      });
      return;
    }

    toast({
      title: "Data Subscription Added",
      description: `${newDataSub.providerName} has been connected successfully.`,
    });
    setIsDataSubOpen(false);
    setNewDataSub({
      providerName: "",
      providerType: "delayed",
      apiKey: "",
      subscriptionTier: "",
    });
  };

  const getStrategyIcon = (type: string) => {
    const strategyType = strategyTypes.find(s => s.value === type);
    if (strategyType) {
      const Icon = strategyType.icon;
      return <Icon className="h-4 w-4" />;
    }
    return <Brain className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Pro-Strategizer</h1>
          <p className="text-muted-foreground">Create and automate your trading strategies</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isDataSubOpen} onOpenChange={setIsDataSubOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Database className="h-4 w-4 mr-2" />
                Add Data Source
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Add Market Data Subscription</DialogTitle>
                <DialogDescription>
                  Connect your market data provider to power your strategies with real-time data.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="provider-name">Provider Name</Label>
                  <Input
                    id="provider-name"
                    placeholder="e.g., Alpha Vantage, Polygon.io, IEX Cloud"
                    value={newDataSub.providerName}
                    onChange={(e) => setNewDataSub({ ...newDataSub, providerName: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="provider-type">Data Type</Label>
                  <Select
                    value={newDataSub.providerType}
                    onValueChange={(value) => setNewDataSub({ ...newDataSub, providerType: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select data type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="realtime">Real-time</SelectItem>
                      <SelectItem value="delayed">Delayed (15 min)</SelectItem>
                      <SelectItem value="historical">Historical Only</SelectItem>
                      <SelectItem value="options">Options Data</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api-key">API Key</Label>
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="Enter your API key"
                    value={newDataSub.apiKey}
                    onChange={(e) => setNewDataSub({ ...newDataSub, apiKey: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sub-tier">Subscription Tier (Optional)</Label>
                  <Input
                    id="sub-tier"
                    placeholder="e.g., Pro, Premium, Enterprise"
                    value={newDataSub.subscriptionTier}
                    onChange={(e) => setNewDataSub({ ...newDataSub, subscriptionTier: e.target.value })}
                  />
                </div>
                <Button onClick={handleAddDataSubscription} className="w-full">
                  <Link2 className="h-4 w-4 mr-2" />
                  Connect Data Source
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          
          <Dialog open={isNewStrategyOpen} onOpenChange={setIsNewStrategyOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Strategy
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Create New Strategy</DialogTitle>
                <DialogDescription>
                  Set up a new automated trading strategy using your connected accounts and data sources.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="strategy-name">Strategy Name *</Label>
                  <Input
                    id="strategy-name"
                    placeholder="e.g., Weekly Tech DCA"
                    value={newStrategy.name}
                    onChange={(e) => setNewStrategy({ ...newStrategy, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="strategy-desc">Description</Label>
                  <Textarea
                    id="strategy-desc"
                    placeholder="Describe your strategy..."
                    value={newStrategy.description}
                    onChange={(e) => setNewStrategy({ ...newStrategy, description: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="strategy-type">Strategy Type *</Label>
                  <Select
                    value={newStrategy.strategyType}
                    onValueChange={(value) => setNewStrategy({ ...newStrategy, strategyType: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select strategy type" />
                    </SelectTrigger>
                    <SelectContent>
                      {strategyTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <type.icon className="h-4 w-4" />
                            {type.label}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="strategy-account">Trading Account *</Label>
                  <Select
                    value={newStrategy.account}
                    onValueChange={(value) => setNewStrategy({ ...newStrategy, account: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      {accounts.map((account) => (
                        <SelectItem key={account.id} value={account.id}>
                          {account.institution_name} ({account.institution_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="strategy-data">Data Source (Optional)</Label>
                  <Select
                    value={newStrategy.dataSubscription}
                    onValueChange={(value) => setNewStrategy({ ...newStrategy, dataSubscription: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select data source" />
                    </SelectTrigger>
                    <SelectContent>
                      {subscriptions.filter(d => d.is_active).map((sub) => (
                        <SelectItem key={sub.id} value={sub.id}>
                          {sub.provider_name} ({sub.provider_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Automated Execution</Label>
                    <p className="text-sm text-muted-foreground">Execute trades automatically</p>
                  </div>
                  <Switch
                    checked={newStrategy.isAutomated}
                    onCheckedChange={(checked) => setNewStrategy({ ...newStrategy, isAutomated: checked })}
                  />
                </div>
                <Button onClick={handleCreateStrategy} className="w-full">
                  Create Strategy
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Strategies</p>
                <p className="text-xl font-bold text-foreground">{strategies.filter(s => s.isActive).length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Automated</p>
                <p className="text-xl font-bold text-foreground">{strategies.filter(s => s.isAutomated && s.isActive).length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Database className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Data Sources</p>
                <p className="text-xl font-bold text-foreground">{subscriptions.filter(d => d.is_active).length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Avg Performance</p>
                <p className="text-xl font-bold text-primary">+6.2%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="trade-analyzer" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trade-analyzer">Trade Analyzer</TabsTrigger>
          <TabsTrigger value="indicator-rules" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Indicator Rules
          </TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
          <TabsTrigger value="data-sources">Data Sources</TabsTrigger>
        </TabsList>

        <TabsContent value="trade-analyzer" className="space-y-4">
          <TradeAnalyzer />
        </TabsContent>

        <TabsContent value="indicator-rules" className="space-y-4">
          <IndicatorTradeRules customIndicators={mockCustomIndicators} />
        </TabsContent>

        <TabsContent value="strategies" className="space-y-4">
          {/* Show Strategy Editor if editing */}
          {editingStrategy ? (
            <StrategyEditor
              strategy={editingStrategy}
              onSave={handleSaveStrategy}
              onCancel={() => setEditingStrategy(null)}
            />
          ) : backtestingStrategy ? (
            <RuleBacktester
              rule={getBacktestRule(backtestingStrategy)}
              onClose={() => setBacktestingStrategy(null)}
            />
          ) : strategies.length === 0 ? (
            <Card className="border-border bg-card">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Brain className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">No Strategies Yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Create your first automated trading strategy to get started.
                </p>
                <Button onClick={() => setIsNewStrategyOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Strategy
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {strategies.map((strategy) => (
                <Card key={strategy.id} className="border-border bg-card">
                  <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${strategy.isActive ? "bg-primary/10" : "bg-secondary"}`}>
                          {getStrategyIcon(strategy.strategyType)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-foreground">{strategy.name}</h3>
                            <Badge variant={strategy.isActive ? "default" : "secondary"}>
                              {strategy.isActive ? "Active" : "Paused"}
                            </Badge>
                            {strategy.isAutomated && (
                              <Badge variant="outline" className="border-primary text-primary">
                                <Zap className="h-3 w-3 mr-1" />
                                Automated
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">{strategy.description}</p>
                          <div className="flex flex-wrap gap-4 text-sm">
                            <span className="text-muted-foreground">
                              Account: <span className="text-foreground">{strategy.account}</span>
                            </span>
                            {strategy.dataSubscription && (
                              <span className="text-muted-foreground">
                                Data: <span className="text-foreground">{strategy.dataSubscription}</span>
                              </span>
                            )}
                            {strategy.lastExecuted && (
                              <span className="text-muted-foreground">
                                Last run: <span className="text-foreground">{strategy.lastExecuted}</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Performance</p>
                          <p className={`font-semibold ${strategy.performance.startsWith("+") ? "text-primary" : "text-destructive"}`}>
                            {strategy.performance}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => handleToggleStrategy(strategy.id)}
                            title={strategy.isActive ? "Pause" : "Activate"}
                          >
                            {strategy.isActive ? (
                              <Pause className="h-4 w-4" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </Button>
                          <Button 
                            variant="outline" 
                            size="icon"
                            onClick={() => setBacktestingStrategy(strategy)}
                            title="Backtest"
                          >
                            <BarChart3 className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="outline" 
                            size="icon"
                            onClick={() => handleEditStrategy(strategy)}
                            title="Edit Strategy"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="outline" 
                            size="icon" 
                            className="text-destructive hover:text-destructive"
                            onClick={() => handleDeleteStrategy(strategy.id)}
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="data-sources" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {subscriptions.map((sub) => (
              <Card key={sub.id} className="border-border bg-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${sub.is_active ? "bg-primary/10" : "bg-secondary"}`}>
                        <Database className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="font-medium text-foreground">{sub.provider_name}</h4>
                        <p className="text-sm text-muted-foreground capitalize">{sub.provider_type} data</p>
                      </div>
                    </div>
                    <Switch checked={sub.is_active || false} />
                  </div>
                  <div className="flex items-center gap-2">
                    {sub.is_active ? (
                      <Badge variant="default" className="bg-primary/10 text-primary border-0">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Connected
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        Disconnected
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            <Card className="border-border bg-card border-dashed">
              <CardContent className="p-4 flex flex-col items-center justify-center h-full min-h-[120px]">
                <Button variant="ghost" onClick={() => setIsDataSubOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Data Source
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
