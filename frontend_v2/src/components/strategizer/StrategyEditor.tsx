import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Plus,
  Trash2,
  Save,
  X,
  TrendingUp,
  TrendingDown,
  ArrowUpDown,
  Target,
  BarChart3,
  Activity,
  Zap,
  AlertTriangle,
  DollarSign,
  Percent,
  Clock,
  Play,
  Settings2,
} from 'lucide-react';
import { toast } from 'sonner';
import { RuleBacktester } from './RuleBacktester';

// Types
export interface IndicatorConfig {
  id: string;
  name: string;
  type: 'sma' | 'ema' | 'rsi' | 'macd' | 'bollinger' | 'vwap' | 'price';
  params: Record<string, number>;
  color: string;
}

export interface StrategyCondition {
  id: string;
  indicatorId: string;
  indicatorName: string;
  operator: 'crosses_above' | 'crosses_below' | 'greater_than' | 'less_than' | 'equals' | 'between';
  compareType: 'value' | 'indicator';
  value: number;
  secondaryValue?: number;
  compareIndicatorId?: string;
}

export interface StrategyEntry {
  enabled: boolean;
  conditions: StrategyCondition[];
  conditionLogic: 'and' | 'or';
  orderType: 'market' | 'limit' | 'stop_limit';
  positionSize: number;
  positionSizeType: 'shares' | 'dollars' | 'percent';
  limitOffset?: number;
  stopOffset?: number;
}

export interface StrategyExit {
  enabled: boolean;
  conditions: StrategyCondition[];
  conditionLogic: 'and' | 'or';
  takeProfitPercent?: number;
  stopLossPercent?: number;
  trailingStopPercent?: number;
  timeBasedExit?: number; // days
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  symbol: string;
  strategyType: string;
  indicators: IndicatorConfig[];
  entry: StrategyEntry;
  exit: StrategyExit;
  isActive: boolean;
  isAutomated: boolean;
  createdAt: string;
  updatedAt: string;
}

interface StrategyEditorProps {
  strategy?: Strategy;
  onSave: (strategy: Strategy) => void;
  onCancel: () => void;
}

const defaultIndicators: IndicatorConfig[] = [
  { id: 'price', name: 'Price', type: 'price', params: {}, color: '#ffffff' },
  { id: 'sma-20', name: 'SMA (20)', type: 'sma', params: { period: 20 }, color: '#3b82f6' },
  { id: 'sma-50', name: 'SMA (50)', type: 'sma', params: { period: 50 }, color: '#60a5fa' },
  { id: 'sma-200', name: 'SMA (200)', type: 'sma', params: { period: 200 }, color: '#93c5fd' },
  { id: 'ema-12', name: 'EMA (12)', type: 'ema', params: { period: 12 }, color: '#8b5cf6' },
  { id: 'ema-26', name: 'EMA (26)', type: 'ema', params: { period: 26 }, color: '#a78bfa' },
  { id: 'rsi-14', name: 'RSI (14)', type: 'rsi', params: { period: 14 }, color: '#f59e0b' },
  { id: 'macd', name: 'MACD', type: 'macd', params: { fast: 12, slow: 26, signal: 9 }, color: '#10b981' },
  { id: 'bollinger', name: 'Bollinger Bands', type: 'bollinger', params: { period: 20, stdDev: 2 }, color: '#ec4899' },
  { id: 'vwap', name: 'VWAP', type: 'vwap', params: {}, color: '#06b6d4' },
];

const conditionOperators = [
  { value: 'crosses_above', label: 'Crosses Above', icon: TrendingUp },
  { value: 'crosses_below', label: 'Crosses Below', icon: TrendingDown },
  { value: 'greater_than', label: 'Greater Than', icon: ArrowUpDown },
  { value: 'less_than', label: 'Less Than', icon: ArrowUpDown },
  { value: 'equals', label: 'Equals', icon: Target },
  { value: 'between', label: 'Between', icon: BarChart3 },
];

const strategyTypes = [
  { value: 'momentum', label: 'Momentum Trading' },
  { value: 'mean_reversion', label: 'Mean Reversion' },
  { value: 'breakout', label: 'Breakout Strategy' },
  { value: 'trend_following', label: 'Trend Following' },
  { value: 'scalping', label: 'Scalping' },
  { value: 'swing', label: 'Swing Trading' },
  { value: 'custom', label: 'Custom Strategy' },
];

const createEmptyStrategy = (): Strategy => ({
  id: `strategy-${Date.now()}`,
  name: '',
  description: '',
  symbol: '',
  strategyType: 'custom',
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
  isActive: false,
  isAutomated: false,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
});

export function StrategyEditor({ strategy, onSave, onCancel }: StrategyEditorProps) {
  const [currentStrategy, setCurrentStrategy] = useState<Strategy>(
    strategy || createEmptyStrategy()
  );
  const [activeTab, setActiveTab] = useState('general');
  const [showBacktest, setShowBacktest] = useState(false);

  // All available indicators (default + strategy custom)
  const allIndicators = [...defaultIndicators, ...currentStrategy.indicators];

  const updateStrategy = (updates: Partial<Strategy>) => {
    setCurrentStrategy(prev => ({ ...prev, ...updates, updatedAt: new Date().toISOString() }));
  };

  const addIndicator = () => {
    const newIndicator: IndicatorConfig = {
      id: `custom-${Date.now()}`,
      name: 'New Indicator',
      type: 'sma',
      params: { period: 20 },
      color: '#' + Math.floor(Math.random()*16777215).toString(16),
    };
    updateStrategy({ indicators: [...currentStrategy.indicators, newIndicator] });
  };

  const updateIndicator = (id: string, updates: Partial<IndicatorConfig>) => {
    updateStrategy({
      indicators: currentStrategy.indicators.map(ind =>
        ind.id === id ? { ...ind, ...updates } : ind
      ),
    });
  };

  const removeIndicator = (id: string) => {
    updateStrategy({
      indicators: currentStrategy.indicators.filter(ind => ind.id !== id),
    });
  };

  const addCondition = (type: 'entry' | 'exit') => {
    const newCondition: StrategyCondition = {
      id: `cond-${Date.now()}`,
      indicatorId: 'price',
      indicatorName: 'Price',
      operator: 'crosses_above',
      compareType: 'indicator',
      value: 0,
      compareIndicatorId: 'sma-20',
    };

    if (type === 'entry') {
      updateStrategy({
        entry: {
          ...currentStrategy.entry,
          conditions: [...currentStrategy.entry.conditions, newCondition],
        },
      });
    } else {
      updateStrategy({
        exit: {
          ...currentStrategy.exit,
          conditions: [...currentStrategy.exit.conditions, newCondition],
        },
      });
    }
  };

  const updateCondition = (type: 'entry' | 'exit', conditionId: string, updates: Partial<StrategyCondition>) => {
    const updateFn = (conditions: StrategyCondition[]) =>
      conditions.map(c => c.id === conditionId ? { ...c, ...updates } : c);

    if (type === 'entry') {
      updateStrategy({
        entry: { ...currentStrategy.entry, conditions: updateFn(currentStrategy.entry.conditions) },
      });
    } else {
      updateStrategy({
        exit: { ...currentStrategy.exit, conditions: updateFn(currentStrategy.exit.conditions) },
      });
    }
  };

  const removeCondition = (type: 'entry' | 'exit', conditionId: string) => {
    if (type === 'entry') {
      updateStrategy({
        entry: {
          ...currentStrategy.entry,
          conditions: currentStrategy.entry.conditions.filter(c => c.id !== conditionId),
        },
      });
    } else {
      updateStrategy({
        exit: {
          ...currentStrategy.exit,
          conditions: currentStrategy.exit.conditions.filter(c => c.id !== conditionId),
        },
      });
    }
  };

  const handleSave = () => {
    if (!currentStrategy.name.trim()) {
      toast.error('Please enter a strategy name');
      return;
    }
    if (!currentStrategy.symbol.trim()) {
      toast.error('Please enter a symbol');
      return;
    }
    onSave(currentStrategy);
  };

  // Convert strategy to trade rule format for backtesting
  const getBacktestRule = () => ({
    id: currentStrategy.id,
    name: currentStrategy.name,
    symbol: currentStrategy.symbol,
    conditions: currentStrategy.entry.conditions.map(c => ({
      id: c.id,
      indicatorId: c.indicatorId,
      indicatorName: c.indicatorName,
      indicatorType: allIndicators.find(i => i.id === c.indicatorId)?.type || 'sma',
      operator: c.operator,
      value: c.value,
      secondaryValue: c.secondaryValue,
    })),
    conditionLogic: currentStrategy.entry.conditionLogic,
    action: 'buy' as const,
    quantity: currentStrategy.entry.positionSize,
  });

  if (showBacktest) {
    return (
      <RuleBacktester
        rule={getBacktestRule()}
        onClose={() => setShowBacktest(false)}
      />
    );
  }

  const renderConditionEditor = (
    condition: StrategyCondition,
    type: 'entry' | 'exit'
  ) => (
    <Card key={condition.id} className="border-border bg-secondary/20">
      <CardContent className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          {/* Indicator Select */}
          <div className="space-y-2">
            <Label className="text-xs">Indicator</Label>
            <Select
              value={condition.indicatorId}
              onValueChange={(value) => {
                const indicator = allIndicators.find(i => i.id === value);
                updateCondition(type, condition.id, {
                  indicatorId: value,
                  indicatorName: indicator?.name || value,
                });
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {allIndicators.map(ind => (
                  <SelectItem key={ind.id} value={ind.id}>
                    {ind.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Operator Select */}
          <div className="space-y-2">
            <Label className="text-xs">Condition</Label>
            <Select
              value={condition.operator}
              onValueChange={(value) => updateCondition(type, condition.id, { operator: value as any })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {conditionOperators.map(op => (
                  <SelectItem key={op.value} value={op.value}>
                    <div className="flex items-center gap-2">
                      <op.icon className="h-3 w-3" />
                      {op.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Compare Type */}
          <div className="space-y-2">
            <Label className="text-xs">Compare To</Label>
            <Select
              value={condition.compareType}
              onValueChange={(value) => updateCondition(type, condition.id, { compareType: value as any })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="indicator">Indicator</SelectItem>
                <SelectItem value="value">Fixed Value</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Value or Indicator */}
          <div className="space-y-2">
            <Label className="text-xs">
              {condition.compareType === 'value' ? 'Value' : 'Indicator'}
            </Label>
            {condition.compareType === 'value' ? (
              <Input
                type="number"
                value={condition.value}
                onChange={(e) => updateCondition(type, condition.id, { value: parseFloat(e.target.value) || 0 })}
              />
            ) : (
              <Select
                value={condition.compareIndicatorId}
                onValueChange={(value) => updateCondition(type, condition.id, { compareIndicatorId: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {allIndicators.filter(i => i.id !== condition.indicatorId).map(ind => (
                    <SelectItem key={ind.id} value={ind.id}>
                      {ind.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Delete Button */}
          <Button
            variant="ghost"
            size="icon"
            className="text-destructive hover:text-destructive"
            onClick={() => removeCondition(type, condition.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        {condition.operator === 'between' && (
          <div className="mt-3">
            <Label className="text-xs">Second Value</Label>
            <Input
              type="number"
              value={condition.secondaryValue || 0}
              onChange={(e) => updateCondition(type, condition.id, { secondaryValue: parseFloat(e.target.value) || 0 })}
              className="w-32"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-primary" />
              {strategy ? 'Edit Strategy' : 'Create Strategy'}
            </CardTitle>
            <CardDescription>
              Configure indicators, entry/exit rules, and risk management
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowBacktest(true)} disabled={!currentStrategy.symbol || currentStrategy.entry.conditions.length === 0}>
              <Play className="h-4 w-4 mr-2" />
              Backtest
            </Button>
            <Button variant="outline" onClick={onCancel}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-2" />
              Save Strategy
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="indicators">Indicators</TabsTrigger>
            <TabsTrigger value="entry">Entry Rules</TabsTrigger>
            <TabsTrigger value="exit">Exit Rules</TabsTrigger>
          </TabsList>

          {/* General Tab */}
          <TabsContent value="general" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Strategy Name *</Label>
                  <Input
                    value={currentStrategy.name}
                    onChange={(e) => updateStrategy({ name: e.target.value })}
                    placeholder="e.g., Golden Cross Momentum"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Symbol *</Label>
                  <Input
                    value={currentStrategy.symbol}
                    onChange={(e) => updateStrategy({ symbol: e.target.value.toUpperCase() })}
                    placeholder="e.g., AAPL"
                    className="font-mono"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Strategy Type</Label>
                  <Select
                    value={currentStrategy.strategyType}
                    onValueChange={(value) => updateStrategy({ strategyType: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {strategyTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    value={currentStrategy.description}
                    onChange={(e) => updateStrategy({ description: e.target.value })}
                    placeholder="Describe your strategy..."
                    rows={4}
                  />
                </div>

                <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
                  <div>
                    <Label>Automated Execution</Label>
                    <p className="text-sm text-muted-foreground">Execute trades automatically when conditions are met</p>
                  </div>
                  <Switch
                    checked={currentStrategy.isAutomated}
                    onCheckedChange={(checked) => updateStrategy({ isAutomated: checked })}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Indicators Tab */}
          <TabsContent value="indicators" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Custom Indicators</h3>
                <p className="text-sm text-muted-foreground">Add and configure indicators for your strategy</p>
              </div>
              <Button onClick={addIndicator}>
                <Plus className="h-4 w-4 mr-2" />
                Add Indicator
              </Button>
            </div>

            {/* Default Indicators */}
            <div className="space-y-2">
              <Label className="text-muted-foreground">Built-in Indicators (always available)</Label>
              <div className="flex flex-wrap gap-2">
                {defaultIndicators.map(ind => (
                  <Badge key={ind.id} variant="outline" style={{ borderColor: ind.color }}>
                    {ind.name}
                  </Badge>
                ))}
              </div>
            </div>

            <Separator />

            {/* Custom Indicators */}
            {currentStrategy.indicators.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <Activity className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">No custom indicators added</p>
                  <Button variant="link" onClick={addIndicator}>
                    Add your first indicator
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {currentStrategy.indicators.map(indicator => (
                  <Card key={indicator.id} className="border-border">
                    <CardContent className="p-4">
                      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
                        <div className="space-y-2">
                          <Label>Name</Label>
                          <Input
                            value={indicator.name}
                            onChange={(e) => updateIndicator(indicator.id, { name: e.target.value })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Type</Label>
                          <Select
                            value={indicator.type}
                            onValueChange={(value) => updateIndicator(indicator.id, { type: value as any })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="sma">SMA</SelectItem>
                              <SelectItem value="ema">EMA</SelectItem>
                              <SelectItem value="rsi">RSI</SelectItem>
                              <SelectItem value="macd">MACD</SelectItem>
                              <SelectItem value="bollinger">Bollinger</SelectItem>
                              <SelectItem value="vwap">VWAP</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Period</Label>
                          <Input
                            type="number"
                            value={indicator.params.period || 20}
                            onChange={(e) => updateIndicator(indicator.id, { params: { ...indicator.params, period: parseInt(e.target.value) || 20 } })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Color</Label>
                          <div className="flex gap-2">
                            <Input
                              type="color"
                              value={indicator.color}
                              onChange={(e) => updateIndicator(indicator.id, { color: e.target.value })}
                              className="w-12 h-10 p-1"
                            />
                            <Input
                              value={indicator.color}
                              onChange={(e) => updateIndicator(indicator.id, { color: e.target.value })}
                              className="flex-1 font-mono"
                            />
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => removeIndicator(indicator.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Entry Rules Tab */}
          <TabsContent value="entry" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Entry Conditions
                </h3>
                <p className="text-sm text-muted-foreground">Define when to open a position</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Label>Logic:</Label>
                  <Select
                    value={currentStrategy.entry.conditionLogic}
                    onValueChange={(value) => updateStrategy({
                      entry: { ...currentStrategy.entry, conditionLogic: value as 'and' | 'or' }
                    })}
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="and">AND</SelectItem>
                      <SelectItem value="or">OR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={() => addCondition('entry')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Condition
                </Button>
              </div>
            </div>

            {currentStrategy.entry.conditions.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <Target className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">No entry conditions defined</p>
                  <Button variant="link" onClick={() => addCondition('entry')}>
                    Add your first entry condition
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {currentStrategy.entry.conditions.map((condition, index) => (
                  <div key={condition.id}>
                    {index > 0 && (
                      <div className="flex items-center justify-center py-2">
                        <Badge variant="outline">{currentStrategy.entry.conditionLogic.toUpperCase()}</Badge>
                      </div>
                    )}
                    {renderConditionEditor(condition, 'entry')}
                  </div>
                ))}
              </div>
            )}

            <Separator />

            {/* Position Sizing */}
            <div className="space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Position Sizing
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Order Type</Label>
                  <Select
                    value={currentStrategy.entry.orderType}
                    onValueChange={(value) => updateStrategy({
                      entry: { ...currentStrategy.entry, orderType: value as any }
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="market">Market Order</SelectItem>
                      <SelectItem value="limit">Limit Order</SelectItem>
                      <SelectItem value="stop_limit">Stop Limit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Size Type</Label>
                  <Select
                    value={currentStrategy.entry.positionSizeType}
                    onValueChange={(value) => updateStrategy({
                      entry: { ...currentStrategy.entry, positionSizeType: value as any }
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="shares">Fixed Shares</SelectItem>
                      <SelectItem value="dollars">Dollar Amount</SelectItem>
                      <SelectItem value="percent">% of Portfolio</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Position Size</Label>
                  <Input
                    type="number"
                    value={currentStrategy.entry.positionSize}
                    onChange={(e) => updateStrategy({
                      entry: { ...currentStrategy.entry, positionSize: parseFloat(e.target.value) || 0 }
                    })}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Exit Rules Tab */}
          <TabsContent value="exit" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-destructive" />
                  Exit Conditions
                </h3>
                <p className="text-sm text-muted-foreground">Define when to close a position</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Label>Logic:</Label>
                  <Select
                    value={currentStrategy.exit.conditionLogic}
                    onValueChange={(value) => updateStrategy({
                      exit: { ...currentStrategy.exit, conditionLogic: value as 'and' | 'or' }
                    })}
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="and">AND</SelectItem>
                      <SelectItem value="or">OR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={() => addCondition('exit')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Condition
                </Button>
              </div>
            </div>

            {currentStrategy.exit.conditions.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <AlertTriangle className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">No indicator-based exit conditions</p>
                  <p className="text-sm text-muted-foreground">Use stop loss and take profit below, or add conditions</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {currentStrategy.exit.conditions.map((condition, index) => (
                  <div key={condition.id}>
                    {index > 0 && (
                      <div className="flex items-center justify-center py-2">
                        <Badge variant="outline">{currentStrategy.exit.conditionLogic.toUpperCase()}</Badge>
                      </div>
                    )}
                    {renderConditionEditor(condition, 'exit')}
                  </div>
                ))}
              </div>
            )}

            <Separator />

            {/* Risk Management */}
            <div className="space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Risk Management
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Percent className="h-3 w-3" />
                    Take Profit %
                  </Label>
                  <Input
                    type="number"
                    value={currentStrategy.exit.takeProfitPercent || ''}
                    onChange={(e) => updateStrategy({
                      exit: { ...currentStrategy.exit, takeProfitPercent: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="e.g., 10"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <AlertTriangle className="h-3 w-3" />
                    Stop Loss %
                  </Label>
                  <Input
                    type="number"
                    value={currentStrategy.exit.stopLossPercent || ''}
                    onChange={(e) => updateStrategy({
                      exit: { ...currentStrategy.exit, stopLossPercent: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="e.g., 5"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <TrendingDown className="h-3 w-3" />
                    Trailing Stop %
                  </Label>
                  <Input
                    type="number"
                    value={currentStrategy.exit.trailingStopPercent || ''}
                    onChange={(e) => updateStrategy({
                      exit: { ...currentStrategy.exit, trailingStopPercent: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="e.g., 5"
                  />
                </div>
              </div>
              <div className="max-w-xs space-y-2">
                <Label className="flex items-center gap-2">
                  <Clock className="h-3 w-3" />
                  Time-Based Exit (days)
                </Label>
                <Input
                  type="number"
                  value={currentStrategy.exit.timeBasedExit || ''}
                  onChange={(e) => updateStrategy({
                    exit: { ...currentStrategy.exit, timeBasedExit: parseInt(e.target.value) || undefined }
                  })}
                  placeholder="e.g., 30"
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
