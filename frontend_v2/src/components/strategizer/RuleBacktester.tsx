import { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from 'recharts';
import {
  Play,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  Calendar,
  DollarSign,
  Percent,
  AlertTriangle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

interface TradeRuleCondition {
  id: string;
  indicatorId: string;
  indicatorName: string;
  indicatorType: string;
  operator: 'crosses_above' | 'crosses_below' | 'greater_than' | 'less_than' | 'equals' | 'between';
  value: number;
  secondaryValue?: number;
}

interface TradeRule {
  id: string;
  name: string;
  symbol: string;
  conditions: TradeRuleCondition[];
  conditionLogic: 'and' | 'or';
  action: 'buy' | 'sell' | 'alert_only';
  quantity: number;
}

interface BacktestResult {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalReturn: number;
  totalReturnPercent: number;
  maxDrawdown: number;
  sharpeRatio: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;
  trades: BacktestTrade[];
  equityCurve: { date: string; equity: number }[];
}

interface BacktestTrade {
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  type: 'buy' | 'sell';
  profit: number;
  profitPercent: number;
  indicatorValues: Record<string, number>;
}

interface RuleBacktesterProps {
  rule: TradeRule;
  onClose?: () => void;
}

// Generate mock historical price data
const generateHistoricalData = (days: number, basePrice: number) => {
  const data: { date: Date; open: number; high: number; low: number; close: number; volume: number }[] = [];
  let price = basePrice * 0.85;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    
    const volatility = basePrice * 0.02;
    const open = price;
    const change = (Math.random() - 0.48) * volatility;
    const close = Math.max(open + change, basePrice * 0.5);
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    
    data.push({
      date,
      open,
      high,
      low,
      close,
      volume: Math.floor(Math.random() * 10000000) + 1000000,
    });
    
    price = close;
  }
  
  return data;
};

// Calculate SMA
const calculateSMA = (prices: number[], period: number): (number | null)[] => {
  const result: (number | null)[] = [];
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      result.push(sum / period);
    }
  }
  return result;
};

// Calculate EMA
const calculateEMA = (prices: number[], period: number): (number | null)[] => {
  const result: (number | null)[] = [];
  const multiplier = 2 / (period + 1);
  let ema: number | null = null;
  
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else if (i === period - 1) {
      ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
      result.push(ema);
    } else {
      ema = (prices[i] - ema!) * multiplier + ema!;
      result.push(ema);
    }
  }
  return result;
};

// Calculate RSI
const calculateRSI = (prices: number[], period: number): (number | null)[] => {
  const result: (number | null)[] = [];
  const changes = prices.map((p, i) => i > 0 ? p - prices[i - 1] : 0);
  
  for (let i = 0; i < prices.length; i++) {
    if (i < period) {
      result.push(null);
    } else {
      const gains = changes.slice(i - period + 1, i + 1).filter(c => c > 0);
      const losses = changes.slice(i - period + 1, i + 1).filter(c => c < 0).map(c => Math.abs(c));
      
      const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / period : 0;
      const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / period : 0;
      
      if (avgLoss === 0) {
        result.push(100);
      } else {
        const rs = avgGain / avgLoss;
        result.push(100 - (100 / (1 + rs)));
      }
    }
  }
  return result;
};

// Evaluate condition at a specific point
const evaluateCondition = (
  condition: TradeRuleCondition,
  currentValue: number | null,
  previousValue: number | null
): boolean => {
  if (currentValue === null) return false;
  
  switch (condition.operator) {
    case 'greater_than':
      return currentValue > condition.value;
    case 'less_than':
      return currentValue < condition.value;
    case 'equals':
      return Math.abs(currentValue - condition.value) < 0.01;
    case 'between':
      return currentValue >= condition.value && currentValue <= (condition.secondaryValue || condition.value);
    case 'crosses_above':
      if (previousValue === null) return false;
      return previousValue <= condition.value && currentValue > condition.value;
    case 'crosses_below':
      if (previousValue === null) return false;
      return previousValue >= condition.value && currentValue < condition.value;
    default:
      return false;
  }
};

export function RuleBacktester({ rule, onClose }: RuleBacktesterProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [lookbackDays, setLookbackDays] = useState('180');
  const [initialCapital, setInitialCapital] = useState('10000');

  const runBacktest = useCallback(async () => {
    setIsRunning(true);
    setProgress(0);
    setResult(null);

    try {
      const days = parseInt(lookbackDays);
      const capital = parseFloat(initialCapital);
      
      // Generate historical data
      const basePrice = 175; // Mock base price
      const historicalData = generateHistoricalData(days, basePrice);
      const closePrices = historicalData.map(d => d.close);
      
      // Calculate all indicators
      const indicatorData: Record<string, (number | null)[]> = {
        'sma-20': calculateSMA(closePrices, 20),
        'sma-50': calculateSMA(closePrices, 50),
        'sma-200': calculateSMA(closePrices, 200),
        'ema-12': calculateEMA(closePrices, 12),
        'ema-26': calculateEMA(closePrices, 26),
        'rsi-14': calculateRSI(closePrices, 14),
      };
      
      setProgress(30);
      
      // Simulate trades
      const trades: BacktestTrade[] = [];
      const equityCurve: { date: string; equity: number }[] = [];
      let equity = capital;
      let position: { entryPrice: number; entryDate: Date; quantity: number } | null = null;
      
      for (let i = 1; i < historicalData.length; i++) {
        const price = historicalData[i].close;
        const date = historicalData[i].date;
        
        // Get indicator values at this point
        const currentValues: Record<string, number | null> = {};
        const previousValues: Record<string, number | null> = {};
        
        for (const [key, values] of Object.entries(indicatorData)) {
          currentValues[key] = values[i];
          previousValues[key] = values[i - 1];
        }
        
        // Evaluate rule conditions
        const conditionResults: boolean[] = [];
        for (const condition of rule.conditions) {
          const current = currentValues[condition.indicatorId];
          const previous = previousValues[condition.indicatorId];
          const result = evaluateCondition(condition, current, previous);
          conditionResults.push(result);
        }
        
        // Check if rule is triggered
        let isTriggered = false;
        if (conditionResults.length > 0) {
          if (rule.conditionLogic === 'and') {
            isTriggered = conditionResults.every(r => r);
          } else {
            isTriggered = conditionResults.some(r => r);
          }
        }
        
        // Execute trades based on rule action
        if (isTriggered && rule.action !== 'alert_only') {
          if (rule.action === 'buy' && !position) {
            // Enter long position
            position = {
              entryPrice: price,
              entryDate: date,
              quantity: Math.floor(equity / price),
            };
          } else if (rule.action === 'sell' && position) {
            // Exit position
            const profit = (price - position.entryPrice) * position.quantity;
            const profitPercent = ((price - position.entryPrice) / position.entryPrice) * 100;
            
            trades.push({
              entryDate: format(position.entryDate, 'yyyy-MM-dd'),
              exitDate: format(date, 'yyyy-MM-dd'),
              entryPrice: position.entryPrice,
              exitPrice: price,
              quantity: position.quantity,
              type: 'buy',
              profit,
              profitPercent,
              indicatorValues: Object.fromEntries(
                Object.entries(currentValues).filter(([_, v]) => v !== null)
              ) as Record<string, number>,
            });
            
            equity += profit;
            position = null;
          }
        }
        
        equityCurve.push({
          date: format(date, 'MMM dd'),
          equity: position ? equity + (price - position.entryPrice) * position.quantity : equity,
        });
        
        setProgress(30 + Math.floor((i / historicalData.length) * 60));
      }
      
      // Close any remaining position
      if (position) {
        const lastPrice = closePrices[closePrices.length - 1];
        const profit = (lastPrice - position.entryPrice) * position.quantity;
        equity += profit;
        
        trades.push({
          entryDate: format(position.entryDate, 'yyyy-MM-dd'),
          exitDate: format(new Date(), 'yyyy-MM-dd'),
          entryPrice: position.entryPrice,
          exitPrice: lastPrice,
          quantity: position.quantity,
          type: 'buy',
          profit,
          profitPercent: ((lastPrice - position.entryPrice) / position.entryPrice) * 100,
          indicatorValues: {},
        });
      }
      
      // Calculate statistics
      const winningTrades = trades.filter(t => t.profit > 0);
      const losingTrades = trades.filter(t => t.profit <= 0);
      const avgWin = winningTrades.length > 0 ? winningTrades.reduce((a, b) => a + b.profit, 0) / winningTrades.length : 0;
      const avgLoss = losingTrades.length > 0 ? Math.abs(losingTrades.reduce((a, b) => a + b.profit, 0) / losingTrades.length) : 0;
      
      // Calculate max drawdown
      let maxEquity = capital;
      let maxDrawdown = 0;
      for (const point of equityCurve) {
        if (point.equity > maxEquity) maxEquity = point.equity;
        const drawdown = ((maxEquity - point.equity) / maxEquity) * 100;
        if (drawdown > maxDrawdown) maxDrawdown = drawdown;
      }
      
      // Calculate Sharpe ratio (simplified)
      const returns = equityCurve.map((e, i) => i > 0 ? (e.equity - equityCurve[i - 1].equity) / equityCurve[i - 1].equity : 0);
      const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
      const stdDev = Math.sqrt(returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length);
      const sharpeRatio = stdDev > 0 ? (avgReturn * 252) / (stdDev * Math.sqrt(252)) : 0;
      
      setProgress(100);
      
      setResult({
        totalTrades: trades.length,
        winningTrades: winningTrades.length,
        losingTrades: losingTrades.length,
        winRate: trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0,
        totalReturn: equity - capital,
        totalReturnPercent: ((equity - capital) / capital) * 100,
        maxDrawdown,
        sharpeRatio,
        averageWin: avgWin,
        averageLoss: avgLoss,
        profitFactor: avgLoss > 0 ? avgWin / avgLoss : avgWin > 0 ? Infinity : 0,
        trades,
        equityCurve,
      });
      
      toast.success('Backtest completed successfully');
    } catch (error) {
      console.error('Backtest error:', error);
      toast.error('Failed to run backtest');
    } finally {
      setIsRunning(false);
    }
  }, [rule, lookbackDays, initialCapital]);

  const resetBacktest = () => {
    setResult(null);
    setProgress(0);
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Backtest: {rule.name}
            </CardTitle>
            <CardDescription>
              Test your rule against historical data for {rule.symbol}
            </CardDescription>
          </div>
          {onClose && (
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Configuration */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <Label>Lookback Period</Label>
            <Select value={lookbackDays} onValueChange={setLookbackDays}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30">30 Days</SelectItem>
                <SelectItem value="90">90 Days</SelectItem>
                <SelectItem value="180">6 Months</SelectItem>
                <SelectItem value="365">1 Year</SelectItem>
                <SelectItem value="730">2 Years</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Initial Capital</Label>
            <Input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(e.target.value)}
              placeholder="10000"
            />
          </div>
          <div className="flex items-end gap-2">
            <Button onClick={runBacktest} disabled={isRunning} className="flex-1">
              <Play className="h-4 w-4 mr-2" />
              {isRunning ? 'Running...' : 'Run Backtest'}
            </Button>
          </div>
          <div className="flex items-end gap-2">
            <Button variant="outline" onClick={resetBacktest} disabled={isRunning}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
          </div>
        </div>

        {/* Progress */}
        {isRunning && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Running backtest...</span>
              <span className="font-medium">{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        )}

        {/* Results */}
        {result && (
          <>
            <Separator />
            
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Total Return</span>
                  </div>
                  <p className={`text-2xl font-bold ${result.totalReturn >= 0 ? 'text-primary' : 'text-destructive'}`}>
                    {result.totalReturn >= 0 ? '+' : ''}{result.totalReturn.toFixed(2)}
                  </p>
                  <p className={`text-sm ${result.totalReturnPercent >= 0 ? 'text-primary' : 'text-destructive'}`}>
                    {result.totalReturnPercent >= 0 ? '+' : ''}{result.totalReturnPercent.toFixed(2)}%
                  </p>
                </CardContent>
              </Card>

              <Card className="border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Win Rate</span>
                  </div>
                  <p className="text-2xl font-bold text-foreground">{result.winRate.toFixed(1)}%</p>
                  <p className="text-sm text-muted-foreground">
                    {result.winningTrades}W / {result.losingTrades}L
                  </p>
                </CardContent>
              </Card>

              <Card className="border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Max Drawdown</span>
                  </div>
                  <p className="text-2xl font-bold text-destructive">-{result.maxDrawdown.toFixed(2)}%</p>
                  <p className="text-sm text-muted-foreground">Peak to trough</p>
                </CardContent>
              </Card>

              <Card className="border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Percent className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Profit Factor</span>
                  </div>
                  <p className="text-2xl font-bold text-foreground">
                    {result.profitFactor === Infinity ? '∞' : result.profitFactor.toFixed(2)}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Avg Win: ${result.averageWin.toFixed(0)}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Equity Curve */}
            <Card className="border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Equity Curve</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={result.equityCurve}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="date" 
                      stroke="hsl(var(--muted-foreground))" 
                      fontSize={12}
                      tickLine={false}
                    />
                    <YAxis 
                      stroke="hsl(var(--muted-foreground))" 
                      fontSize={12}
                      tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                      formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
                    />
                    <ReferenceLine 
                      y={parseFloat(initialCapital)} 
                      stroke="hsl(var(--muted-foreground))" 
                      strokeDasharray="5 5" 
                    />
                    <defs>
                      <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="equity"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      fill="url(#equityGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Trade History */}
            {result.trades.length > 0 && (
              <Card className="border-border">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Trade History</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[200px]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Entry</TableHead>
                          <TableHead>Exit</TableHead>
                          <TableHead className="text-right">Entry Price</TableHead>
                          <TableHead className="text-right">Exit Price</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead className="text-right">P/L</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.trades.map((trade, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-mono text-sm">{trade.entryDate}</TableCell>
                            <TableCell className="font-mono text-sm">{trade.exitDate}</TableCell>
                            <TableCell className="text-right">${trade.entryPrice.toFixed(2)}</TableCell>
                            <TableCell className="text-right">${trade.exitPrice.toFixed(2)}</TableCell>
                            <TableCell className="text-right">{trade.quantity}</TableCell>
                            <TableCell className={`text-right font-medium ${trade.profit >= 0 ? 'text-primary' : 'text-destructive'}`}>
                              {trade.profit >= 0 ? '+' : ''}{trade.profit.toFixed(2)} ({trade.profitPercent.toFixed(1)}%)
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}

            {result.trades.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No trades were executed during the backtest period.</p>
                <p className="text-sm mt-1">Try adjusting your rule conditions or lookback period.</p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
