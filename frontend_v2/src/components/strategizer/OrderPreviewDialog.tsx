import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { 
  AlertTriangle, 
  CheckCircle, 
  Loader2, 
  TrendingUp, 
  TrendingDown,
  Shield,
  Zap,
  Target,
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';

interface OrderPreviewProps {
  symbol: string;
  quantity: number;
  side: 'buy' | 'sell';
  orderType: 'market' | 'limit';
  limitPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  credentials: {
    api_key: string;
    api_secret: string;
  };
  broker: 'alpaca' | 'interactive_brokers';
  onOrderSubmitted?: (order: any) => void;
  onClose?: () => void;
}

interface OrderPreview {
  symbol: string;
  side: string;
  quantity: number;
  type: string;
  limit_price: number | null;
  estimated_price: number;
  estimated_total: number;
  commission: number;
  fees: number;
  total_cost: number;
  buying_power: number;
  can_execute: boolean;
  account_status: string;
  day_trade_count: number;
  pattern_day_trader: boolean;
}

export function OrderPreviewDialog({
  symbol,
  quantity,
  side,
  orderType,
  limitPrice,
  stopLoss,
  takeProfit,
  credentials,
  broker,
  onOrderSubmitted,
  onClose,
}: OrderPreviewProps) {
  const [preview, setPreview] = useState<OrderPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usePaperTrading, setUsePaperTrading] = useState(true);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const fetchPreview = async () => {
    setLoading(true);
    setError(null);

    try {
      const { data, error: fetchError } = await supabase.functions.invoke('trade-execution', {
        body: {
          action: 'preview',
          symbol,
          quantity,
          side,
          type: orderType,
          limit_price: limitPrice,
          broker,
          credentials,
        },
      });

      if (fetchError) throw fetchError;
      if (data?.error) throw new Error(data.error);

      setPreview(data.preview);
    } catch (err: unknown) {
      console.error('Error fetching order preview:', err);
      setError(err instanceof Error ? err.message : 'Failed to preview order');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitOrder = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const { data, error: submitError } = await supabase.functions.invoke('trade-execution', {
        body: {
          action: 'submit',
          symbol,
          quantity,
          side,
          type: orderType,
          time_in_force: 'day',
          limit_price: limitPrice,
          stop_loss: stopLoss,
          take_profit: takeProfit,
          broker,
          credentials,
          paper_trading: usePaperTrading,
        },
      });

      if (submitError) throw submitError;
      if (data?.error) throw new Error(data.error);

      toast.success(`Order submitted successfully! Order ID: ${data.order.order_id}`);
      onOrderSubmitted?.(data.order);
      setShowConfirmDialog(false);
    } catch (err: unknown) {
      console.error('Error submitting order:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit order');
      toast.error(err instanceof Error ? err.message : 'Failed to submit order');
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  // Fetch preview on mount
  if (!preview && !loading && !error) {
    fetchPreview();
  }

  return (
    <>
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {side === 'buy' ? (
              <TrendingUp className="h-5 w-5 text-primary" />
            ) : (
              <TrendingDown className="h-5 w-5 text-destructive" />
            )}
            Order Preview
          </CardTitle>
          <CardDescription>
            Review your order details before submitting
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span className="text-muted-foreground">Fetching order preview...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30">
              <p className="text-destructive">{error}</p>
              <Button onClick={fetchPreview} variant="outline" size="sm" className="mt-2">
                Try Again
              </Button>
            </div>
          ) : preview ? (
            <>
              {/* Order Summary */}
              <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="text-lg font-bold text-foreground">{symbol}</h4>
                    <div className="flex items-center gap-2">
                      <Badge variant={side === 'buy' ? 'default' : 'destructive'}>
                        {side.toUpperCase()}
                      </Badge>
                      <Badge variant="outline">
                        {orderType === 'market' ? (
                          <><Zap className="h-3 w-3 mr-1" />Market</>
                        ) : (
                          <><Target className="h-3 w-3 mr-1" />Limit</>
                        )}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Quantity</p>
                    <p className="text-2xl font-bold text-foreground">{quantity}</p>
                  </div>
                </div>

                <Separator className="my-4" />

                {/* Price Details */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Estimated Price</span>
                    <span className="font-medium">{formatCurrency(preview.estimated_price)}</span>
                  </div>
                  {preview.limit_price && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Limit Price</span>
                      <span className="font-medium">{formatCurrency(preview.limit_price)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="font-medium">{formatCurrency(preview.estimated_total)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Commission</span>
                    <span className="font-medium text-primary">{formatCurrency(preview.commission)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fees (SEC/FINRA)</span>
                    <span className="font-medium">{formatCurrency(preview.fees)}</span>
                  </div>
                  <Separator className="my-2" />
                  <div className="flex justify-between text-lg">
                    <span className="font-semibold">Total Cost</span>
                    <span className="font-bold text-foreground">{formatCurrency(preview.total_cost)}</span>
                  </div>
                </div>
              </div>

              {/* Stop Loss / Take Profit */}
              {(stopLoss || takeProfit) && (
                <div className="grid gap-4 md:grid-cols-2">
                  {stopLoss && (
                    <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-destructive" />
                        <span className="text-sm text-muted-foreground">Stop Loss</span>
                      </div>
                      <p className="text-lg font-bold text-destructive">{formatCurrency(stopLoss)}</p>
                    </div>
                  )}
                  {takeProfit && (
                    <div className="p-3 rounded-lg bg-primary/10 border border-primary/30">
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-primary" />
                        <span className="text-sm text-muted-foreground">Take Profit</span>
                      </div>
                      <p className="text-lg font-bold text-primary">{formatCurrency(takeProfit)}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Account Status */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border">
                <div>
                  <p className="text-sm text-muted-foreground">Buying Power</p>
                  <p className="font-medium text-foreground">{formatCurrency(preview.buying_power)}</p>
                </div>
                <div className="flex items-center gap-2">
                  {preview.can_execute ? (
                    <Badge variant="default" className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Ready to Execute
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" />
                      Insufficient Funds
                    </Badge>
                  )}
                </div>
              </div>

              {/* PDT Warning */}
              {preview.pattern_day_trader && (
                <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm font-medium text-yellow-500">Pattern Day Trader</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Day trades this week: {preview.day_trade_count}
                  </p>
                </div>
              )}

              {/* Paper Trading Toggle */}
              <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  <Label htmlFor="paper-trading">Paper Trading Mode</Label>
                </div>
                <Switch
                  id="paper-trading"
                  checked={usePaperTrading}
                  onCheckedChange={setUsePaperTrading}
                />
              </div>

              {!usePaperTrading && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                    <span className="text-sm font-medium text-destructive">LIVE TRADING ENABLED</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    This order will execute with real money!
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  disabled={!preview.can_execute || submitting}
                  onClick={() => setShowConfirmDialog(true)}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Submitting...
                    </>
                  ) : (
                    <>Submit Order</>
                  )}
                </Button>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Order Submission</AlertDialogTitle>
            <AlertDialogDescription>
              You are about to {side} {quantity} shares of {symbol} at{' '}
              {orderType === 'market' ? 'market price' : `$${limitPrice}`}.
              {!usePaperTrading && (
                <span className="block mt-2 text-destructive font-medium">
                  ⚠️ This is a LIVE order that will execute with real money!
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleSubmitOrder} disabled={submitting}>
              {submitting ? 'Submitting...' : 'Confirm Order'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
