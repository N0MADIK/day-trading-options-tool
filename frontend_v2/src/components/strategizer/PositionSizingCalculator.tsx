import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Calculator, 
  Shield, 
  TrendingDown, 
  DollarSign,
  Percent,
  AlertTriangle,
  Info,
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PositionSizingCalculatorProps {
  accountBalance: number;
  currentPrice: number;
  symbol?: string;
  onQuantityChange?: (quantity: number) => void;
  stopLossPrice?: number;
}

type RiskModel = 'fixed_percent' | 'kelly' | 'optimal_f';

export function PositionSizingCalculator({
  accountBalance,
  currentPrice,
  symbol = '',
  onQuantityChange,
  stopLossPrice,
}: PositionSizingCalculatorProps) {
  const [riskPercent, setRiskPercent] = useState(2);
  const [riskModel, setRiskModel] = useState<RiskModel>('fixed_percent');
  const [customStopLoss, setCustomStopLoss] = useState(stopLossPrice?.toString() || '');
  const [winRate, setWinRate] = useState(55);
  const [avgWinLoss, setAvgWinLoss] = useState(1.5);

  const effectiveStopLoss = parseFloat(customStopLoss) || stopLossPrice || currentPrice * 0.95;
  const riskPerShare = currentPrice - effectiveStopLoss;

  const calculations = useMemo(() => {
    if (!currentPrice || currentPrice <= 0 || !accountBalance || accountBalance <= 0) {
      return null;
    }

    const maxRiskAmount = accountBalance * (riskPercent / 100);
    
    // Calculate based on risk model
    let adjustedRiskPercent = riskPercent;
    
    if (riskModel === 'kelly') {
      // Kelly Criterion: f = (bp - q) / b
      // where b = win/loss ratio, p = win rate, q = 1 - p
      const p = winRate / 100;
      const q = 1 - p;
      const b = avgWinLoss;
      const kellyPercent = ((b * p - q) / b) * 100;
      // Use half Kelly for safety
      adjustedRiskPercent = Math.max(0, Math.min(kellyPercent / 2, 25));
    } else if (riskModel === 'optimal_f') {
      // Simplified optimal f calculation
      const p = winRate / 100;
      const b = avgWinLoss;
      const optimalF = ((b + 1) * p - 1) / b;
      adjustedRiskPercent = Math.max(0, Math.min(optimalF * 100 / 2, 25));
    }

    const effectiveRiskAmount = accountBalance * (adjustedRiskPercent / 100);
    
    // Position size based on stop loss
    let suggestedQuantity = 0;
    if (riskPerShare > 0) {
      suggestedQuantity = Math.floor(effectiveRiskAmount / riskPerShare);
    } else {
      // If no stop loss or it's above current price, use max risk / price
      suggestedQuantity = Math.floor(effectiveRiskAmount / currentPrice);
    }

    const positionValue = suggestedQuantity * currentPrice;
    const portfolioPercent = (positionValue / accountBalance) * 100;
    const maxLoss = suggestedQuantity * riskPerShare;
    const breakeven = currentPrice;

    // Risk level assessment
    let riskLevel: 'low' | 'moderate' | 'high' | 'extreme' = 'low';
    if (portfolioPercent > 50) riskLevel = 'extreme';
    else if (portfolioPercent > 25) riskLevel = 'high';
    else if (portfolioPercent > 10) riskLevel = 'moderate';

    return {
      maxRiskAmount: effectiveRiskAmount,
      suggestedQuantity,
      positionValue,
      portfolioPercent,
      maxLoss,
      riskLevel,
      breakeven,
      adjustedRiskPercent,
    };
  }, [accountBalance, currentPrice, riskPercent, riskPerShare, riskModel, winRate, avgWinLoss]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-primary';
      case 'moderate': return 'text-yellow-500';
      case 'high': return 'text-orange-500';
      case 'extreme': return 'text-destructive';
      default: return 'text-muted-foreground';
    }
  };

  const getRiskBadgeVariant = (level: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (level) {
      case 'low': return 'default';
      case 'moderate': return 'secondary';
      case 'high': return 'destructive';
      case 'extreme': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Position Sizing Calculator
          {symbol && <Badge variant="outline">{symbol}</Badge>}
        </CardTitle>
        <CardDescription>
          Calculate optimal position size based on your risk tolerance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Account Info */}
        <div className="grid gap-4 md:grid-cols-3">
          <div className="p-3 rounded-lg bg-secondary/50 border border-border">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <DollarSign className="h-4 w-4" />
              Account Balance
            </div>
            <p className="text-xl font-bold text-foreground">{formatCurrency(accountBalance)}</p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/50 border border-border">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              Current Price
            </div>
            <p className="text-xl font-bold text-foreground">{formatCurrency(currentPrice)}</p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/50 border border-border">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <TrendingDown className="h-4 w-4" />
              Stop Loss
            </div>
            <p className="text-xl font-bold text-foreground">{formatCurrency(effectiveStopLoss)}</p>
          </div>
        </div>

        <Separator />

        {/* Risk Settings */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Risk Model
                </Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p><strong>Fixed %:</strong> Risk a fixed percentage per trade</p>
                      <p><strong>Kelly:</strong> Optimal sizing based on win rate and win/loss ratio</p>
                      <p><strong>Optimal F:</strong> More aggressive Kelly variant</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <Select value={riskModel} onValueChange={(v) => setRiskModel(v as RiskModel)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fixed_percent">Fixed Percentage</SelectItem>
                  <SelectItem value="kelly">Kelly Criterion (Half)</SelectItem>
                  <SelectItem value="optimal_f">Optimal F (Half)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Percent className="h-4 w-4" />
                  Risk per Trade
                </Label>
                <span className="text-sm font-medium">{riskPercent}%</span>
              </div>
              <Slider
                value={[riskPercent]}
                onValueChange={(v) => setRiskPercent(v[0])}
                min={0.5}
                max={10}
                step={0.5}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Conservative (0.5%)</span>
                <span>Aggressive (10%)</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Stop Loss Price</Label>
              <Input
                type="number"
                step="0.01"
                placeholder={`e.g., ${(currentPrice * 0.95).toFixed(2)}`}
                value={customStopLoss}
                onChange={(e) => setCustomStopLoss(e.target.value)}
              />
              {riskPerShare > 0 && (
                <p className="text-xs text-muted-foreground">
                  Risk per share: {formatCurrency(riskPerShare)} ({((riskPerShare / currentPrice) * 100).toFixed(1)}%)
                </p>
              )}
            </div>
          </div>

          {/* Kelly/Optimal F inputs */}
          {(riskModel === 'kelly' || riskModel === 'optimal_f') && (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Historical Win Rate</Label>
                  <span className="text-sm font-medium">{winRate}%</span>
                </div>
                <Slider
                  value={[winRate]}
                  onValueChange={(v) => setWinRate(v[0])}
                  min={30}
                  max={80}
                  step={1}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Avg Win / Avg Loss Ratio</Label>
                  <span className="text-sm font-medium">{avgWinLoss.toFixed(1)}x</span>
                </div>
                <Slider
                  value={[avgWinLoss]}
                  onValueChange={(v) => setAvgWinLoss(v[0])}
                  min={0.5}
                  max={5}
                  step={0.1}
                  className="w-full"
                />
              </div>

              {calculations && calculations.adjustedRiskPercent !== riskPercent && (
                <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                  <p className="text-sm text-foreground">
                    <strong>{riskModel === 'kelly' ? 'Half Kelly' : 'Half Optimal F'}:</strong>{' '}
                    {calculations.adjustedRiskPercent.toFixed(2)}% suggested
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <Separator />

        {/* Results */}
        {calculations && (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                <p className="text-sm text-muted-foreground mb-1">Suggested Quantity</p>
                <p className="text-2xl font-bold text-primary">{calculations.suggestedQuantity}</p>
                <p className="text-xs text-muted-foreground">shares</p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                <p className="text-sm text-muted-foreground mb-1">Position Value</p>
                <p className="text-xl font-bold text-foreground">{formatCurrency(calculations.positionValue)}</p>
                <p className="text-xs text-muted-foreground">{calculations.portfolioPercent.toFixed(1)}% of portfolio</p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                <p className="text-sm text-muted-foreground mb-1">Max Risk Amount</p>
                <p className="text-xl font-bold text-destructive">{formatCurrency(calculations.maxRiskAmount)}</p>
                <p className="text-xs text-muted-foreground">{calculations.adjustedRiskPercent.toFixed(1)}% of account</p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                <p className="text-sm text-muted-foreground mb-1">Max Loss (at stop)</p>
                <p className="text-xl font-bold text-destructive">{formatCurrency(calculations.maxLoss)}</p>
                <p className="text-xs text-muted-foreground">if stop hit</p>
              </div>
            </div>

            {/* Risk Assessment */}
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${
              calculations.riskLevel === 'extreme' ? 'bg-destructive/10 border-destructive/30' :
              calculations.riskLevel === 'high' ? 'bg-orange-500/10 border-orange-500/30' :
              calculations.riskLevel === 'moderate' ? 'bg-yellow-500/10 border-yellow-500/30' :
              'bg-primary/10 border-primary/30'
            }`}>
              {(calculations.riskLevel === 'high' || calculations.riskLevel === 'extreme') && (
                <AlertTriangle className={`h-5 w-5 ${getRiskColor(calculations.riskLevel)}`} />
              )}
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant={getRiskBadgeVariant(calculations.riskLevel)}>
                    {calculations.riskLevel.toUpperCase()} RISK
                  </Badge>
                  <span className={`text-sm font-medium ${getRiskColor(calculations.riskLevel)}`}>
                    {calculations.portfolioPercent.toFixed(1)}% portfolio concentration
                  </span>
                </div>
                {calculations.riskLevel === 'extreme' && (
                  <p className="text-sm text-muted-foreground mt-1">
                    Consider reducing position size to maintain diversification
                  </p>
                )}
              </div>
            </div>

            {/* Apply Button */}
            {onQuantityChange && calculations.suggestedQuantity > 0 && (
              <div className="flex justify-end">
                <button
                  onClick={() => onQuantityChange(calculations.suggestedQuantity)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Apply {calculations.suggestedQuantity} shares
                </button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
