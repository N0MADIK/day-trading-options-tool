import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Plus,
  Trash2,
  Edit2,
  AlertTriangle,
  CheckCircle,
  Zap,
  Target,
  BarChart3,
  ArrowUpDown,
  Play,
  Pause,
  Info,
  Bell,
  Mail,
  Radio,
  ChevronDown,
  History,
  Eye,
} from 'lucide-react';
import { toast } from 'sonner';
import { useRuleMonitor, RuleTriggerEvent, TradeRule as MonitorTradeRule } from '@/hooks/useRuleMonitor';
import { RuleBacktester } from './RuleBacktester';
import { format } from 'date-fns';

// Indicator types from Market Scanner
export interface IndicatorConfig {
  id: string;
  name: string;
  type: 'sma' | 'ema' | 'rsi' | 'macd' | 'bollinger' | 'vwap' | 'custom';
  enabled: boolean;
  color: string;
  params: Record<string, number>;
}

// Trade rule condition operators
type ConditionOperator = 'crosses_above' | 'crosses_below' | 'greater_than' | 'less_than' | 'equals' | 'between';

// Trade action types
type TradeActionType = 'buy' | 'sell' | 'alert_only';
type OrderType = 'market' | 'limit' | 'stop_limit';

export interface TradeRuleCondition {
  id: string;
  indicatorId: string;
  indicatorName: string;
  indicatorType: string;
  operator: ConditionOperator;
  value: number;
  secondaryValue?: number;
  compareToIndicator?: string;
}

export interface TradeRule {
  id: string;
  name: string;
  symbol: string;
  enabled: boolean;
  conditions: TradeRuleCondition[];
  conditionLogic: 'and' | 'or';
  action: TradeActionType;
  orderType: OrderType;
  quantity: number;
  limitPrice?: number;
  stopPrice?: number;
  notifyEmail: boolean;
  notifyPush: boolean;
  createdAt: string;
  lastTriggered?: string;
  triggerCount: number;
}

// Default indicators that are always available
const defaultIndicators: IndicatorConfig[] = [
  { id: 'sma-20', name: 'SMA (20)', type: 'sma', enabled: true, color: '#3b82f6', params: { period: 20 } },
  { id: 'sma-50', name: 'SMA (50)', type: 'sma', enabled: true, color: '#60a5fa', params: { period: 50 } },
  { id: 'sma-200', name: 'SMA (200)', type: 'sma', enabled: true, color: '#93c5fd', params: { period: 200 } },
  { id: 'ema-12', name: 'EMA (12)', type: 'ema', enabled: true, color: '#8b5cf6', params: { period: 12 } },
  { id: 'ema-26', name: 'EMA (26)', type: 'ema', enabled: true, color: '#a78bfa', params: { period: 26 } },
  { id: 'rsi-14', name: 'RSI (14)', type: 'rsi', enabled: true, color: '#f59e0b', params: { period: 14, overbought: 70, oversold: 30 } },
  { id: 'macd', name: 'MACD', type: 'macd', enabled: true, color: '#10b981', params: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 } },
  { id: 'bollinger', name: 'Bollinger Bands', type: 'bollinger', enabled: true, color: '#ec4899', params: { period: 20, stdDev: 2 } },
  { id: 'vwap', name: 'VWAP', type: 'vwap', enabled: true, color: '#06b6d4', params: {} },
];

const conditionOperators: { value: ConditionOperator; label: string; icon: React.ReactNode }[] = [
  { value: 'crosses_above', label: 'Crosses Above', icon: <TrendingUp className="h-4 w-4" /> },
  { value: 'crosses_below', label: 'Crosses Below', icon: <TrendingDown className="h-4 w-4" /> },
  { value: 'greater_than', label: 'Greater Than', icon: <ArrowUpDown className="h-4 w-4" /> },
  { value: 'less_than', label: 'Less Than', icon: <ArrowUpDown className="h-4 w-4" /> },
  { value: 'equals', label: 'Equals', icon: <Target className="h-4 w-4" /> },
  { value: 'between', label: 'Between', icon: <BarChart3 className="h-4 w-4" /> },
];

interface IndicatorTradeRulesProps {
  customIndicators?: IndicatorConfig[];
}

export function IndicatorTradeRules({ customIndicators = [] }: IndicatorTradeRulesProps) {
  const [rules, setRules] = useState<TradeRule[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<TradeRule | null>(null);
  const [backtestingRule, setBacktestingRule] = useState<TradeRule | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [newRule, setNewRule] = useState<Partial<TradeRule>>({
    name: '',
    symbol: '',
    enabled: true,
    conditions: [],
    conditionLogic: 'and',
    action: 'alert_only',
    orderType: 'market',
    quantity: 1,
    notifyEmail: true,
    notifyPush: false,
    triggerCount: 0,
  });
  const [newCondition, setNewCondition] = useState<Partial<TradeRuleCondition>>({
    operator: 'crosses_above',
    value: 0,
  });

  // Convert TradeRule to MonitorTradeRule format
  const monitorRules: MonitorTradeRule[] = rules.map(r => ({
    ...r,
    notifyEmail: r.notifyEmail ?? true,
    notifyPush: r.notifyPush ?? false,
  }));

  // Rule monitoring hook
  const {
    isMonitoring,
    lastCheck,
    triggeredRules,
    startMonitoring,
    stopMonitoring,
    requestNotificationPermission,
  } = useRuleMonitor({
    rules: monitorRules,
    pollingInterval: 30000,
    onRuleTriggered: (event: RuleTriggerEvent) => {
      // Update trigger count for the rule
      setRules(prev => prev.map(r => 
        r.id === event.ruleId 
          ? { ...r, triggerCount: r.triggerCount + 1, lastTriggered: event.triggeredAt.toISOString() }
          : r
      ));
    },
  });

  // Combine default and custom indicators
  const allIndicators = [...defaultIndicators, ...customIndicators];

  const resetForm = () => {
    setNewRule({
      name: '',
      symbol: '',
      enabled: true,
      conditions: [],
      conditionLogic: 'and',
      action: 'alert_only',
      orderType: 'market',
      quantity: 1,
      notifyEmail: true,
      notifyPush: false,
      triggerCount: 0,
    });
    setNewCondition({
      operator: 'crosses_above',
      value: 0,
    });
    setEditingRule(null);
  };

  const handleAddCondition = () => {
    if (!newCondition.indicatorId) {
      toast.error('Please select an indicator');
      return;
    }

    const indicator = allIndicators.find(i => i.id === newCondition.indicatorId);
    if (!indicator) return;

    const condition: TradeRuleCondition = {
      id: `cond-${Date.now()}`,
      indicatorId: indicator.id,
      indicatorName: indicator.name,
      indicatorType: indicator.type,
      operator: newCondition.operator || 'crosses_above',
      value: newCondition.value || 0,
      secondaryValue: newCondition.secondaryValue,
      compareToIndicator: newCondition.compareToIndicator,
    };

    setNewRule(prev => ({
      ...prev,
      conditions: [...(prev.conditions || []), condition],
    }));

    setNewCondition({
      operator: 'crosses_above',
      value: 0,
    });
  };

  const handleRemoveCondition = (conditionId: string) => {
    setNewRule(prev => ({
      ...prev,
      conditions: (prev.conditions || []).filter(c => c.id !== conditionId),
    }));
  };

  const handleCreateRule = () => {
    if (!newRule.name || !newRule.symbol || (newRule.conditions?.length || 0) === 0) {
      toast.error('Please fill in all required fields and add at least one condition');
      return;
    }

    const rule: TradeRule = {
      id: editingRule?.id || `rule-${Date.now()}`,
      name: newRule.name!,
      symbol: newRule.symbol!.toUpperCase(),
      enabled: newRule.enabled ?? true,
      conditions: newRule.conditions || [],
      conditionLogic: newRule.conditionLogic || 'and',
      action: newRule.action || 'alert_only',
      orderType: newRule.orderType || 'market',
      quantity: newRule.quantity || 1,
      limitPrice: newRule.limitPrice,
      stopPrice: newRule.stopPrice,
      notifyEmail: newRule.notifyEmail ?? true,
      notifyPush: newRule.notifyPush ?? false,
      createdAt: editingRule?.createdAt || new Date().toISOString(),
      lastTriggered: editingRule?.lastTriggered,
      triggerCount: editingRule?.triggerCount || 0,
    };

    if (editingRule) {
      setRules(prev => prev.map(r => r.id === editingRule.id ? rule : r));
      toast.success('Trade rule updated');
    } else {
      setRules(prev => [...prev, rule]);
      toast.success('Trade rule created');
    }

    setIsCreateOpen(false);
    resetForm();
  };

  const handleEditRule = (rule: TradeRule) => {
    setEditingRule(rule);
    setNewRule({
      name: rule.name,
      symbol: rule.symbol,
      enabled: rule.enabled,
      conditions: [...rule.conditions],
      conditionLogic: rule.conditionLogic,
      action: rule.action,
      orderType: rule.orderType,
      quantity: rule.quantity,
      limitPrice: rule.limitPrice,
      stopPrice: rule.stopPrice,
      notifyEmail: rule.notifyEmail,
      notifyPush: rule.notifyPush,
      triggerCount: rule.triggerCount,
    });
    setIsCreateOpen(true);
  };

  const handleDeleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(r => r.id !== ruleId));
    toast.success('Trade rule deleted');
  };

  const handleToggleRule = (ruleId: string) => {
    setRules(prev => prev.map(r => 
      r.id === ruleId ? { ...r, enabled: !r.enabled } : r
    ));
  };

  const handleEnablePushNotifications = async () => {
    const granted = await requestNotificationPermission();
    if (granted) {
      toast.success('Push notifications enabled');
    } else {
      toast.error('Push notifications denied');
    }
  };

  const getIndicatorIcon = (type: string) => {
    switch (type) {
      case 'sma':
      case 'ema':
        return <TrendingUp className="h-4 w-4 text-primary" />;
      case 'rsi':
        return <Activity className="h-4 w-4 text-amber-500" />;
      case 'macd':
        return <BarChart3 className="h-4 w-4 text-emerald-500" />;
      case 'bollinger':
        return <Target className="h-4 w-4 text-pink-500" />;
      case 'vwap':
        return <Zap className="h-4 w-4 text-cyan-500" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getConditionDescription = (condition: TradeRuleCondition) => {
    const operatorLabel = conditionOperators.find(o => o.value === condition.operator)?.label || condition.operator;
    if (condition.operator === 'between') {
      return `${condition.indicatorName} ${operatorLabel} ${condition.value} and ${condition.secondaryValue}`;
    }
    if (condition.compareToIndicator) {
      const compareIndicator = allIndicators.find(i => i.id === condition.compareToIndicator);
      return `${condition.indicatorName} ${operatorLabel} ${compareIndicator?.name || 'Unknown'}`;
    }
    return `${condition.indicatorName} ${operatorLabel} ${condition.value}`;
  };

  // Show backtester if a rule is selected
  if (backtestingRule) {
    return (
      <RuleBacktester 
        rule={backtestingRule} 
        onClose={() => setBacktestingRule(null)} 
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Monitoring Status Card */}
      <Card className={`border-border ${isMonitoring ? 'bg-primary/5 border-primary/30' : 'bg-card'}`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${isMonitoring ? 'bg-primary/20 animate-pulse' : 'bg-secondary'}`}>
                <Radio className={`h-5 w-5 ${isMonitoring ? 'text-primary' : 'text-muted-foreground'}`} />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">
                  {isMonitoring ? 'Monitoring Active' : 'Monitoring Paused'}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {isMonitoring 
                    ? `Last check: ${lastCheck ? format(lastCheck, 'HH:mm:ss') : 'Starting...'}`
                    : `${rules.filter(r => r.enabled).length} rules ready to monitor`
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleEnablePushNotifications}
              >
                <Bell className="h-4 w-4 mr-2" />
                Enable Push
              </Button>
              <Button
                variant={isMonitoring ? 'destructive' : 'default'}
                onClick={isMonitoring ? stopMonitoring : startMonitoring}
                disabled={rules.filter(r => r.enabled).length === 0}
              >
                {isMonitoring ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Stop Monitoring
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Start Monitoring
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trigger History */}
      {triggeredRules.length > 0 && (
        <Collapsible open={showHistory} onOpenChange={setShowHistory}>
          <Card className="border-border bg-card">
            <CollapsibleTrigger asChild>
              <CardHeader className="cursor-pointer hover:bg-secondary/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <History className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">Trigger History</CardTitle>
                    <Badge variant="secondary">{triggeredRules.length}</Badge>
                  </div>
                  <ChevronDown className={`h-5 w-5 transition-transform ${showHistory ? 'rotate-180' : ''}`} />
                </div>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent>
                <ScrollArea className="h-[200px]">
                  <div className="space-y-2">
                    {triggeredRules.map((event, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border">
                        <div className="flex items-center gap-3">
                          <Badge variant={event.action === 'buy' ? 'default' : event.action === 'sell' ? 'destructive' : 'secondary'}>
                            {event.action.toUpperCase()}
                          </Badge>
                          <div>
                            <p className="font-medium">{event.ruleName}</p>
                            <p className="text-sm text-muted-foreground">{event.symbol}</p>
                          </div>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {format(event.triggeredAt, 'MMM dd, HH:mm:ss')}
                        </span>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      )}

      {/* Trade Rules */}
      <Card className="border-border bg-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                Indicator-Based Trade Rules
              </CardTitle>
              <CardDescription>
                Set up automated trade triggers based on technical indicators from Market Scanner
              </CardDescription>
            </div>
            <Dialog open={isCreateOpen} onOpenChange={(open) => {
              setIsCreateOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Rule
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>{editingRule ? 'Edit Trade Rule' : 'Create Trade Rule'}</DialogTitle>
                  <DialogDescription>
                    Define conditions using technical indicators to trigger trades automatically
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 py-4">
                  {/* Basic Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Rule Name *</Label>
                      <Input
                        placeholder="e.g., Golden Cross Buy Signal"
                        value={newRule.name || ''}
                        onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Symbol *</Label>
                      <Input
                        placeholder="e.g., AAPL"
                        value={newRule.symbol || ''}
                        onChange={(e) => setNewRule({ ...newRule, symbol: e.target.value.toUpperCase() })}
                      />
                    </div>
                  </div>

                  <Separator />

                  {/* Conditions Section */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label className="text-base">Conditions</Label>
                      <div className="flex items-center gap-2">
                        <Label className="text-sm text-muted-foreground">Logic:</Label>
                        <Select
                          value={newRule.conditionLogic}
                          onValueChange={(v) => setNewRule({ ...newRule, conditionLogic: v as 'and' | 'or' })}
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
                    </div>

                    {/* Existing Conditions */}
                    {(newRule.conditions?.length || 0) > 0 && (
                      <div className="space-y-2">
                        {newRule.conditions?.map((condition, index) => (
                          <div key={condition.id} className="flex items-center gap-2 p-3 rounded-lg bg-secondary/30 border border-border">
                            {index > 0 && (
                              <Badge variant="outline" className="mr-2">{newRule.conditionLogic?.toUpperCase()}</Badge>
                            )}
                            {getIndicatorIcon(condition.indicatorType)}
                            <span className="flex-1 text-sm">{getConditionDescription(condition)}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveCondition(condition.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Add New Condition */}
                    <div className="p-4 rounded-lg border border-dashed border-border space-y-4">
                      <Label className="text-sm text-muted-foreground">Add Condition</Label>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-2">
                          <Label className="text-xs">Indicator</Label>
                          <Select
                            value={newCondition.indicatorId}
                            onValueChange={(v) => setNewCondition({ ...newCondition, indicatorId: v })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select indicator" />
                            </SelectTrigger>
                            <SelectContent>
                              {customIndicators.length > 0 && (
                                <>
                                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Custom Indicators</div>
                                  {customIndicators.map((ind) => (
                                    <SelectItem key={ind.id} value={ind.id}>
                                      <div className="flex items-center gap-2">
                                        {getIndicatorIcon(ind.type)}
                                        {ind.name}
                                      </div>
                                    </SelectItem>
                                  ))}
                                  <Separator className="my-1" />
                                </>
                              )}
                              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Standard Indicators</div>
                              {defaultIndicators.map((ind) => (
                                <SelectItem key={ind.id} value={ind.id}>
                                  <div className="flex items-center gap-2">
                                    {getIndicatorIcon(ind.type)}
                                    {ind.name}
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs">Operator</Label>
                          <Select
                            value={newCondition.operator}
                            onValueChange={(v) => setNewCondition({ ...newCondition, operator: v as ConditionOperator })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {conditionOperators.map((op) => (
                                <SelectItem key={op.value} value={op.value}>
                                  <div className="flex items-center gap-2">
                                    {op.icon}
                                    {op.label}
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs">Value</Label>
                          <div className="flex gap-2">
                            <Input
                              type="number"
                              placeholder="Value"
                              value={newCondition.value || ''}
                              onChange={(e) => setNewCondition({ ...newCondition, value: parseFloat(e.target.value) })}
                            />
                            {newCondition.operator === 'between' && (
                              <Input
                                type="number"
                                placeholder="To"
                                value={newCondition.secondaryValue || ''}
                                onChange={(e) => setNewCondition({ ...newCondition, secondaryValue: parseFloat(e.target.value) })}
                              />
                            )}
                          </div>
                        </div>
                      </div>
                      <Button variant="outline" size="sm" onClick={handleAddCondition}>
                        <Plus className="h-4 w-4 mr-2" />
                        Add Condition
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  {/* Trade Action */}
                  <div className="space-y-4">
                    <Label className="text-base">Trade Action</Label>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs">Action Type</Label>
                        <Select
                          value={newRule.action}
                          onValueChange={(v) => setNewRule({ ...newRule, action: v as TradeActionType })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="alert_only">
                              <div className="flex items-center gap-2">
                                <AlertTriangle className="h-4 w-4 text-amber-500" />
                                Alert Only
                              </div>
                            </SelectItem>
                            <SelectItem value="buy">
                              <div className="flex items-center gap-2">
                                <TrendingUp className="h-4 w-4 text-primary" />
                                Buy
                              </div>
                            </SelectItem>
                            <SelectItem value="sell">
                              <div className="flex items-center gap-2">
                                <TrendingDown className="h-4 w-4 text-destructive" />
                                Sell
                              </div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {newRule.action !== 'alert_only' && (
                        <>
                          <div className="space-y-2">
                            <Label className="text-xs">Order Type</Label>
                            <Select
                              value={newRule.orderType}
                              onValueChange={(v) => setNewRule({ ...newRule, orderType: v as OrderType })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="market">Market</SelectItem>
                                <SelectItem value="limit">Limit</SelectItem>
                                <SelectItem value="stop_limit">Stop Limit</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label className="text-xs">Quantity</Label>
                            <Input
                              type="number"
                              value={newRule.quantity || ''}
                              onChange={(e) => setNewRule({ ...newRule, quantity: parseInt(e.target.value) })}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  <Separator />

                  {/* Notification Settings */}
                  <div className="space-y-4">
                    <Label className="text-base">Notifications</Label>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <Label>Email Notifications</Label>
                        </div>
                        <Switch
                          checked={newRule.notifyEmail}
                          onCheckedChange={(checked) => setNewRule({ ...newRule, notifyEmail: checked })}
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                        <div className="flex items-center gap-2">
                          <Bell className="h-4 w-4 text-muted-foreground" />
                          <Label>Push Notifications</Label>
                        </div>
                        <Switch
                          checked={newRule.notifyPush}
                          onCheckedChange={(checked) => setNewRule({ ...newRule, notifyPush: checked })}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={newRule.enabled}
                        onCheckedChange={(checked) => setNewRule({ ...newRule, enabled: checked })}
                      />
                      <Label>Enable rule immediately</Label>
                    </div>
                    <Button onClick={handleCreateRule}>
                      {editingRule ? 'Update Rule' : 'Create Rule'}
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {rules.length === 0 ? (
            <div className="text-center py-12">
              <Zap className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No Trade Rules Yet</h3>
              <p className="text-muted-foreground mb-4">
                Create rules using technical indicators to automate your trading signals
              </p>
              <Button variant="outline" onClick={() => setIsCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Rule
              </Button>
            </div>
          ) : (
            <div className="rounded-lg border border-border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">Status</TableHead>
                    <TableHead>Rule</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Conditions</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Notifications</TableHead>
                    <TableHead className="text-right">Triggered</TableHead>
                    <TableHead className="w-32">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleToggleRule(rule.id)}
                              >
                                {rule.enabled ? (
                                  <CheckCircle className="h-5 w-5 text-primary" />
                                ) : (
                                  <Pause className="h-5 w-5 text-muted-foreground" />
                                )}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              {rule.enabled ? 'Active - Click to pause' : 'Paused - Click to activate'}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{rule.name}</p>
                          <p className="text-xs text-muted-foreground">
                            Created {format(new Date(rule.createdAt), 'MMM dd, yyyy')}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">{rule.symbol}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {rule.conditions.slice(0, 2).map((cond, idx) => (
                            <Badge key={cond.id} variant="secondary" className="text-xs">
                              {idx > 0 && <span className="mr-1 text-muted-foreground">{rule.conditionLogic.toUpperCase()}</span>}
                              {cond.indicatorType.toUpperCase()}
                            </Badge>
                          ))}
                          {rule.conditions.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{rule.conditions.length - 2} more
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={rule.action === 'buy' ? 'default' : rule.action === 'sell' ? 'destructive' : 'secondary'}
                        >
                          {rule.action === 'alert_only' ? 'Alert' : rule.action.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {rule.notifyEmail && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Mail className="h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>Email notifications enabled</TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                          {rule.notifyPush && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Bell className="h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>Push notifications enabled</TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {rule.triggerCount}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setBacktestingRule(rule)}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Backtest</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditRule(rule)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteRule(rule.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Info Section */}
          {rules.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-secondary/30 border border-border">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                <div className="text-sm text-muted-foreground">
                  <p>Trade rules are evaluated every 30 seconds when monitoring is active. Connect a brokerage account to enable automatic trade execution.</p>
                  <p className="mt-1">Click the eye icon to backtest a rule against historical data before activating it.</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
