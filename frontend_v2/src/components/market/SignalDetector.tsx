import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  TrendingUp,
  TrendingDown,
  Plus,
  Trash2,
  Target,
  BarChart3,
  Activity,
  Zap,
  Bell,
  ChevronDown,
  Play,
  Pause,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowUpDown,
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { ChartDataPoint } from './InteractiveChart';

// Types
export interface SignalCondition {
  id: string;
  indicatorId: string;
  indicatorName: string;
  operator: 'crosses_above' | 'crosses_below' | 'greater_than' | 'less_than' | 'between';
  value: number;
  secondaryValue?: number;
  compareIndicatorId?: string;
}

export interface SignalRule {
  id: string;
  name: string;
  enabled: boolean;
  signalType: 'buy' | 'sell';
  conditions: SignalCondition[];
  conditionLogic: 'and' | 'or';
  createdAt: string;
}

export interface Signal {
  id: string;
  ruleId: string;
  ruleName: string;
  signalType: 'buy' | 'sell';
  symbol: string;
  price: number;
  timestamp: Date;
  indicators: Record<string, number>;
}

interface SignalDetectorProps {
  symbol: string;
  currentPrice: number;
  chartData: ChartDataPoint[];
  onSignalDetected?: (signal: Signal) => void;
}

const defaultIndicators = [
  { id: 'price', name: 'Price' },
  { id: 'sma-20', name: 'SMA (20)' },
  { id: 'sma-50', name: 'SMA (50)' },
  { id: 'sma-200', name: 'SMA (200)' },
  { id: 'ema-12', name: 'EMA (12)' },
  { id: 'ema-26', name: 'EMA (26)' },
  { id: 'rsi-14', name: 'RSI (14)' },
];

const conditionOperators = [
  { value: 'crosses_above', label: 'Crosses Above', icon: TrendingUp },
  { value: 'crosses_below', label: 'Crosses Below', icon: TrendingDown },
  { value: 'greater_than', label: 'Greater Than', icon: ArrowUpDown },
  { value: 'less_than', label: 'Less Than', icon: ArrowUpDown },
  { value: 'between', label: 'Between', icon: BarChart3 },
];

// Calculate indicators from chart data
const calculateIndicators = (data: ChartDataPoint[]) => {
  if (data.length < 200) return {};
  
  const closes = data.map(d => d.close);
  const lastIndex = closes.length - 1;
  
  // SMA calculations
  const sma = (period: number) => {
    if (lastIndex < period - 1) return null;
    return closes.slice(lastIndex - period + 1, lastIndex + 1).reduce((a, b) => a + b, 0) / period;
  };
  
  // EMA calculations
  const ema = (period: number) => {
    if (lastIndex < period - 1) return null;
    const multiplier = 2 / (period + 1);
    let emaVal = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
    for (let i = period; i <= lastIndex; i++) {
      emaVal = (closes[i] - emaVal) * multiplier + emaVal;
    }
    return emaVal;
  };
  
  // RSI calculation
  const rsi = (period: number) => {
    if (lastIndex < period) return null;
    const changes = closes.slice(lastIndex - period, lastIndex + 1).map((p, i, arr) => 
      i > 0 ? p - arr[i - 1] : 0
    );
    const gains = changes.filter(c => c > 0);
    const losses = changes.filter(c => c < 0).map(c => Math.abs(c));
    const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / period : 0;
    const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / period : 0;
    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  };
  
  return {
    'price': closes[lastIndex],
    'sma-20': sma(20),
    'sma-50': sma(50),
    'sma-200': sma(200),
    'ema-12': ema(12),
    'ema-26': ema(26),
    'rsi-14': rsi(14),
  };
};

// Check if condition is met
const evaluateCondition = (
  condition: SignalCondition,
  indicators: Record<string, number | null>,
  prevIndicators: Record<string, number | null>
): boolean => {
  const current = indicators[condition.indicatorId];
  const previous = prevIndicators[condition.indicatorId];
  
  if (current === null || current === undefined) return false;
  
  // For crossing conditions
  if (condition.operator === 'crosses_above' || condition.operator === 'crosses_below') {
    if (previous === null || previous === undefined) return false;
    
    let compareValue = condition.value;
    let prevCompareValue = condition.value;
    
    if (condition.compareIndicatorId) {
      const compareInd = indicators[condition.compareIndicatorId];
      const prevCompareInd = prevIndicators[condition.compareIndicatorId];
      if (compareInd === null || compareInd === undefined) return false;
      compareValue = compareInd;
      prevCompareValue = prevCompareInd ?? compareInd;
    }
    
    if (condition.operator === 'crosses_above') {
      return previous <= prevCompareValue && current > compareValue;
    } else {
      return previous >= prevCompareValue && current < compareValue;
    }
  }
  
  // For comparison conditions
  let compareValue = condition.value;
  if (condition.compareIndicatorId) {
    const compareInd = indicators[condition.compareIndicatorId];
    if (compareInd === null || compareInd === undefined) return false;
    compareValue = compareInd;
  }
  
  switch (condition.operator) {
    case 'greater_than':
      return current > compareValue;
    case 'less_than':
      return current < compareValue;
    case 'between':
      return current >= condition.value && current <= (condition.secondaryValue ?? condition.value);
    default:
      return false;
  }
};

// Default signal rules
const defaultRules: SignalRule[] = [
  {
    id: 'golden-cross',
    name: 'Golden Cross',
    enabled: true,
    signalType: 'buy',
    conditions: [
      { id: 'gc-1', indicatorId: 'sma-50', indicatorName: 'SMA (50)', operator: 'crosses_above', value: 0, compareIndicatorId: 'sma-200' }
    ],
    conditionLogic: 'and',
    createdAt: new Date().toISOString(),
  },
  {
    id: 'death-cross',
    name: 'Death Cross',
    enabled: true,
    signalType: 'sell',
    conditions: [
      { id: 'dc-1', indicatorId: 'sma-50', indicatorName: 'SMA (50)', operator: 'crosses_below', value: 0, compareIndicatorId: 'sma-200' }
    ],
    conditionLogic: 'and',
    createdAt: new Date().toISOString(),
  },
  {
    id: 'rsi-oversold',
    name: 'RSI Oversold',
    enabled: true,
    signalType: 'buy',
    conditions: [
      { id: 'rsi-os-1', indicatorId: 'rsi-14', indicatorName: 'RSI (14)', operator: 'crosses_above', value: 30 }
    ],
    conditionLogic: 'and',
    createdAt: new Date().toISOString(),
  },
  {
    id: 'rsi-overbought',
    name: 'RSI Overbought',
    enabled: true,
    signalType: 'sell',
    conditions: [
      { id: 'rsi-ob-1', indicatorId: 'rsi-14', indicatorName: 'RSI (14)', operator: 'crosses_below', value: 70 }
    ],
    conditionLogic: 'and',
    createdAt: new Date().toISOString(),
  },
];

export function SignalDetector({ symbol, currentPrice, chartData, onSignalDetected }: SignalDetectorProps) {
  const [rules, setRules] = useState<SignalRule[]>(defaultRules);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [newRule, setNewRule] = useState<Partial<SignalRule>>({
    name: '',
    signalType: 'buy',
    conditions: [],
    conditionLogic: 'and',
    enabled: true,
  });
  const [newCondition, setNewCondition] = useState<Partial<SignalCondition>>({
    operator: 'crosses_above',
    value: 0,
  });

  // Calculate current indicators
  const indicators = useMemo(() => calculateIndicators(chartData), [chartData]);
  
  // Calculate previous indicators (simulated - would need historical data in production)
  const prevIndicators = useMemo(() => {
    if (chartData.length < 2) return {};
    const prevData = chartData.slice(0, -1);
    return calculateIndicators(prevData);
  }, [chartData]);

  // Check for signals
  const activeSignals = useMemo(() => {
    const detected: Signal[] = [];
    
    rules.filter(r => r.enabled).forEach(rule => {
      const results = rule.conditions.map(condition => 
        evaluateCondition(condition, indicators, prevIndicators)
      );
      
      const isTriggered = rule.conditionLogic === 'and'
        ? results.every(r => r)
        : results.some(r => r);
      
      if (isTriggered) {
        detected.push({
          id: `signal-${Date.now()}-${rule.id}`,
          ruleId: rule.id,
          ruleName: rule.name,
          signalType: rule.signalType,
          symbol,
          price: currentPrice,
          timestamp: new Date(),
          indicators: Object.fromEntries(
            Object.entries(indicators).filter(([_, v]) => v !== null)
          ) as Record<string, number>,
        });
      }
    });
    
    return detected;
  }, [rules, indicators, prevIndicators, symbol, currentPrice]);

  const handleToggleRule = (ruleId: string) => {
    setRules(prev => prev.map(r => 
      r.id === ruleId ? { ...r, enabled: !r.enabled } : r
    ));
  };

  const handleDeleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(r => r.id !== ruleId));
    toast.success('Signal rule deleted');
  };

  const handleAddCondition = () => {
    if (!newCondition.indicatorId) {
      toast.error('Please select an indicator');
      return;
    }

    const indicator = defaultIndicators.find(i => i.id === newCondition.indicatorId);
    const condition: SignalCondition = {
      id: `cond-${Date.now()}`,
      indicatorId: newCondition.indicatorId!,
      indicatorName: indicator?.name || '',
      operator: newCondition.operator || 'crosses_above',
      value: newCondition.value || 0,
      secondaryValue: newCondition.secondaryValue,
      compareIndicatorId: newCondition.compareIndicatorId,
    };

    setNewRule(prev => ({
      ...prev,
      conditions: [...(prev.conditions || []), condition],
    }));

    setNewCondition({ operator: 'crosses_above', value: 0 });
  };

  const handleRemoveCondition = (conditionId: string) => {
    setNewRule(prev => ({
      ...prev,
      conditions: (prev.conditions || []).filter(c => c.id !== conditionId),
    }));
  };

  const handleCreateRule = () => {
    if (!newRule.name || (newRule.conditions?.length || 0) === 0) {
      toast.error('Please enter a name and add at least one condition');
      return;
    }

    const rule: SignalRule = {
      id: `rule-${Date.now()}`,
      name: newRule.name!,
      enabled: true,
      signalType: newRule.signalType || 'buy',
      conditions: newRule.conditions || [],
      conditionLogic: newRule.conditionLogic || 'and',
      createdAt: new Date().toISOString(),
    };

    setRules(prev => [...prev, rule]);
    toast.success('Signal rule created');
    setIsCreateOpen(false);
    setNewRule({
      name: '',
      signalType: 'buy',
      conditions: [],
      conditionLogic: 'and',
      enabled: true,
    });
  };

  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring);
    toast.success(isMonitoring ? 'Signal monitoring paused' : 'Signal monitoring started');
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              Signal Detector
            </CardTitle>
            <CardDescription>
              Detect buy/sell signals based on indicator rules
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={isMonitoring ? 'destructive' : 'default'}
              size="sm"
              onClick={toggleMonitoring}
            >
              {isMonitoring ? (
                <><Pause className="h-4 w-4 mr-2" />Stop</>
              ) : (
                <><Play className="h-4 w-4 mr-2" />Monitor</>
              )}
            </Button>
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Rule
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>Create Signal Rule</DialogTitle>
                  <DialogDescription>
                    Define conditions to detect buy/sell signals
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Rule Name</Label>
                      <Input
                        value={newRule.name}
                        onChange={(e) => setNewRule(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., Golden Cross"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Signal Type</Label>
                      <Select
                        value={newRule.signalType}
                        onValueChange={(value) => setNewRule(prev => ({ ...prev, signalType: value as 'buy' | 'sell' }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="buy">
                            <span className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4 text-primary" />
                              Buy Signal
                            </span>
                          </SelectItem>
                          <SelectItem value="sell">
                            <span className="flex items-center gap-2">
                              <TrendingDown className="h-4 w-4 text-destructive" />
                              Sell Signal
                            </span>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <Separator />

                  {/* Conditions */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>Conditions</Label>
                      <Select
                        value={newRule.conditionLogic}
                        onValueChange={(value) => setNewRule(prev => ({ ...prev, conditionLogic: value as 'and' | 'or' }))}
                      >
                        <SelectTrigger className="w-20">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="and">AND</SelectItem>
                          <SelectItem value="or">OR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {newRule.conditions?.map(condition => (
                      <div key={condition.id} className="flex items-center gap-2 p-2 rounded bg-secondary/50">
                        <Badge variant="outline">{condition.indicatorName}</Badge>
                        <span className="text-sm text-muted-foreground">{condition.operator.replace('_', ' ')}</span>
                        <span className="text-sm font-mono">
                          {condition.compareIndicatorId 
                            ? defaultIndicators.find(i => i.id === condition.compareIndicatorId)?.name 
                            : condition.value}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="ml-auto h-6 w-6"
                          onClick={() => handleRemoveCondition(condition.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}

                    {/* Add condition form */}
                    <div className="grid grid-cols-4 gap-2 p-3 rounded bg-secondary/30">
                      <Select
                        value={newCondition.indicatorId}
                        onValueChange={(value) => setNewCondition(prev => ({ ...prev, indicatorId: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Indicator" />
                        </SelectTrigger>
                        <SelectContent>
                          {defaultIndicators.map(ind => (
                            <SelectItem key={ind.id} value={ind.id}>{ind.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      <Select
                        value={newCondition.operator}
                        onValueChange={(value) => setNewCondition(prev => ({ ...prev, operator: value as any }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {conditionOperators.map(op => (
                            <SelectItem key={op.value} value={op.value}>{op.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      <Select
                        value={newCondition.compareIndicatorId || 'value'}
                        onValueChange={(value) => setNewCondition(prev => ({
                          ...prev,
                          compareIndicatorId: value === 'value' ? undefined : value,
                        }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Compare to" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="value">Fixed Value</SelectItem>
                          {defaultIndicators.filter(i => i.id !== newCondition.indicatorId).map(ind => (
                            <SelectItem key={ind.id} value={ind.id}>{ind.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      {!newCondition.compareIndicatorId && (
                        <Input
                          type="number"
                          value={newCondition.value}
                          onChange={(e) => setNewCondition(prev => ({ ...prev, value: parseFloat(e.target.value) || 0 }))}
                          placeholder="Value"
                        />
                      )}

                      <Button onClick={handleAddCondition} className="col-span-4">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Condition
                      </Button>
                    </div>
                  </div>

                  <Button onClick={handleCreateRule} className="w-full">
                    Create Signal Rule
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Active Signals Alert */}
        {activeSignals.length > 0 && (
          <Card className={`border-2 ${activeSignals[0].signalType === 'buy' ? 'border-primary bg-primary/10' : 'border-destructive bg-destructive/10'}`}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-full ${activeSignals[0].signalType === 'buy' ? 'bg-primary/20' : 'bg-destructive/20'}`}>
                  {activeSignals[0].signalType === 'buy' 
                    ? <TrendingUp className="h-5 w-5 text-primary" />
                    : <TrendingDown className="h-5 w-5 text-destructive" />
                  }
                </div>
                <div className="flex-1">
                  <p className="font-semibold">
                    {activeSignals.length} Active Signal{activeSignals.length > 1 ? 's' : ''} Detected!
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {activeSignals.map(s => s.ruleName).join(', ')}
                  </p>
                </div>
                <Badge variant={activeSignals[0].signalType === 'buy' ? 'default' : 'destructive'} className="text-lg px-3 py-1">
                  {activeSignals[0].signalType.toUpperCase()}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Current Indicators */}
        <div className="grid grid-cols-3 md:grid-cols-7 gap-2">
          {defaultIndicators.map(ind => (
            <div key={ind.id} className="p-2 rounded bg-secondary/30 text-center">
              <p className="text-xs text-muted-foreground truncate">{ind.name}</p>
              <p className="font-mono text-sm font-semibold">
                {indicators[ind.id] !== null && indicators[ind.id] !== undefined
                  ? typeof indicators[ind.id] === 'number' 
                    ? (indicators[ind.id] as number).toFixed(ind.id.includes('rsi') ? 1 : 2)
                    : '-'
                  : '-'}
              </p>
            </div>
          ))}
        </div>

        <Separator />

        {/* Signal Rules */}
        <div className="space-y-2">
          <Label className="text-muted-foreground">Signal Rules</Label>
          <ScrollArea className="h-[200px]">
            <div className="space-y-2">
              {rules.map(rule => (
                <div
                  key={rule.id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    rule.enabled ? 'border-border bg-secondary/20' : 'border-border/50 bg-secondary/10 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={rule.enabled}
                      onCheckedChange={() => handleToggleRule(rule.id)}
                    />
                    <div className="flex items-center gap-2">
                      {rule.signalType === 'buy' ? (
                        <TrendingUp className="h-4 w-4 text-primary" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-destructive" />
                      )}
                      <span className="font-medium">{rule.name}</span>
                    </div>
                    <Badge variant={rule.signalType === 'buy' ? 'default' : 'destructive'} className="text-xs">
                      {rule.signalType.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {rule.conditions.length} condition{rule.conditions.length !== 1 ? 's' : ''}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive"
                      onClick={() => handleDeleteRule(rule.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Signal History */}
        {signals.length > 0 && (
          <Collapsible open={showHistory} onOpenChange={setShowHistory}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between">
                <span className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Signal History ({signals.length})
                </span>
                <ChevronDown className={`h-4 w-4 transition-transform ${showHistory ? 'rotate-180' : ''}`} />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <ScrollArea className="h-[150px] mt-2">
                <div className="space-y-2">
                  {signals.map(signal => (
                    <div key={signal.id} className="flex items-center justify-between p-2 rounded bg-secondary/20">
                      <div className="flex items-center gap-2">
                        <Badge variant={signal.signalType === 'buy' ? 'default' : 'destructive'}>
                          {signal.signalType.toUpperCase()}
                        </Badge>
                        <span className="text-sm">{signal.ruleName}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-mono">${signal.price.toFixed(2)}</p>
                        <p className="text-xs text-muted-foreground">
                          {format(signal.timestamp, 'HH:mm:ss')}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}
