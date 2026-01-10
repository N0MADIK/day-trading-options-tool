import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { 
  Loader2, 
  RefreshCw, 
  XCircle, 
  CheckCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  History,
  ListOrdered,
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { format } from 'date-fns';
import { toast } from 'sonner';

interface Order {
  order_id: string;
  client_order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  filled_quantity: number;
  type: string;
  status: string;
  limit_price: number | null;
  stop_price: number | null;
  filled_avg_price: number | null;
  created_at: string;
  submitted_at: string;
  filled_at: string | null;
}

interface OrderManagementProps {
  credentials: {
    api_key: string;
    api_secret: string;
  };
  paperTrading?: boolean;
  onRefresh?: () => void;
}

export function OrderManagement({
  credentials,
  paperTrading = true,
  onRefresh,
}: OrderManagementProps) {
  const [openOrders, setOpenOrders] = useState<Order[]>([]);
  const [orderHistory, setOrderHistory] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [cancelingOrder, setCancelingOrder] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('open');

  const fetchOrders = useCallback(async (status: 'open' | 'all' = 'open') => {
    if (!credentials.api_key || !credentials.api_secret) return;

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('trade-execution', {
        body: {
          action: 'get_orders',
          credentials,
          paper_trading: paperTrading,
          status,
        },
      });

      if (error) throw error;
      if (data?.error) throw new Error(data.error);

      if (status === 'open') {
        setOpenOrders(data.orders || []);
      } else {
        // Filter out open orders for history view
        const closed = (data.orders || []).filter((o: Order) => 
          !['new', 'accepted', 'pending_new', 'partially_filled'].includes(o.status)
        );
        setOrderHistory(closed);
      }
    } catch (err: unknown) {
      console.error('Error fetching orders:', err);
      toast.error('Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  }, [credentials, paperTrading]);

  const handleCancelOrder = async (orderId: string) => {
    setCancelingOrder(orderId);
    try {
      const { data, error } = await supabase.functions.invoke('trade-execution', {
        body: {
          action: 'cancel',
          order_id: orderId,
          credentials,
          paper_trading: paperTrading,
        },
      });

      if (error) throw error;
      if (data?.error) throw new Error(data.error);

      toast.success('Order cancelled successfully');
      fetchOrders('open');
      onRefresh?.();
    } catch (err: unknown) {
      console.error('Error cancelling order:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to cancel order');
    } finally {
      setCancelingOrder(null);
    }
  };

  useEffect(() => {
    if (credentials.api_key && credentials.api_secret) {
      fetchOrders('open');
    }
  }, [fetchOrders]);

  useEffect(() => {
    if (activeTab === 'history' && orderHistory.length === 0) {
      fetchOrders('all');
    }
  }, [activeTab, orderHistory.length, fetchOrders]);

  const formatCurrency = (value: number | null) => {
    if (value === null) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled':
        return (
          <Badge variant="default" className="flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            Filled
          </Badge>
        );
      case 'new':
      case 'accepted':
      case 'pending_new':
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        );
      case 'partially_filled':
        return (
          <Badge variant="outline" className="flex items-center gap-1 border-yellow-500 text-yellow-500">
            <Clock className="h-3 w-3" />
            Partial
          </Badge>
        );
      case 'canceled':
      case 'cancelled':
        return (
          <Badge variant="outline" className="flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            Cancelled
          </Badge>
        );
      case 'rejected':
      case 'expired':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {status}
          </Badge>
        );
    }
  };

  if (!credentials.api_key || !credentials.api_secret) {
    return (
      <Card className="border-border bg-card">
        <CardContent className="p-6 text-center text-muted-foreground">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
          <p>Connect your Alpaca credentials to view orders</p>
          <p className="text-sm mt-1">Go to Connections → Market Data to add Alpaca API keys</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ListOrdered className="h-5 w-5" />
              Order Management
            </CardTitle>
            <CardDescription>
              View and manage your open orders and trade history
              {paperTrading && (
                <Badge variant="secondary" className="ml-2">Paper Trading</Badge>
              )}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchOrders('open');
              if (activeTab === 'history') fetchOrders('all');
            }}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="open" className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Open Orders
              {openOrders.length > 0 && (
                <Badge variant="secondary" className="ml-1">{openOrders.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="h-4 w-4" />
              Order History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="open" className="mt-4">
            {loading && openOrders.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                <span className="text-muted-foreground">Loading orders...</span>
              </div>
            ) : openOrders.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No open orders</p>
              </div>
            ) : (
              <ScrollArea className="h-[300px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Filled</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Time</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {openOrders.map((order) => (
                      <TableRow key={order.order_id}>
                        <TableCell className="font-medium">{order.symbol}</TableCell>
                        <TableCell>
                          <div className={`flex items-center gap-1 ${
                            order.side === 'buy' ? 'text-primary' : 'text-destructive'
                          }`}>
                            {order.side === 'buy' ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            {order.side.toUpperCase()}
                          </div>
                        </TableCell>
                        <TableCell className="capitalize">{order.type}</TableCell>
                        <TableCell className="text-right">{order.quantity}</TableCell>
                        <TableCell className="text-right">{order.filled_quantity}</TableCell>
                        <TableCell className="text-right">
                          {order.limit_price ? formatCurrency(order.limit_price) : 'Market'}
                        </TableCell>
                        <TableCell>{getStatusBadge(order.status)}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {format(new Date(order.submitted_at), 'HH:mm:ss')}
                        </TableCell>
                        <TableCell>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={cancelingOrder === order.order_id}
                              >
                                {cancelingOrder === order.order_id ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <XCircle className="h-4 w-4 text-destructive" />
                                )}
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Cancel Order</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to cancel this {order.side} order for {order.quantity} shares of {order.symbol}?
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Keep Order</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleCancelOrder(order.order_id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Cancel Order
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            )}
          </TabsContent>

          <TabsContent value="history" className="mt-4">
            {loading && orderHistory.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                <span className="text-muted-foreground">Loading history...</span>
              </div>
            ) : orderHistory.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No order history</p>
              </div>
            ) : (
              <ScrollArea className="h-[300px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Filled</TableHead>
                      <TableHead className="text-right">Avg Price</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orderHistory.map((order) => (
                      <TableRow key={order.order_id}>
                        <TableCell className="font-medium">{order.symbol}</TableCell>
                        <TableCell>
                          <div className={`flex items-center gap-1 ${
                            order.side === 'buy' ? 'text-primary' : 'text-destructive'
                          }`}>
                            {order.side === 'buy' ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            {order.side.toUpperCase()}
                          </div>
                        </TableCell>
                        <TableCell className="capitalize">{order.type}</TableCell>
                        <TableCell className="text-right">{order.quantity}</TableCell>
                        <TableCell className="text-right">{order.filled_quantity}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(order.filled_avg_price)}
                        </TableCell>
                        <TableCell>{getStatusBadge(order.status)}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {order.filled_at 
                            ? format(new Date(order.filled_at), 'MMM d, HH:mm')
                            : format(new Date(order.submitted_at), 'MMM d, HH:mm')
                          }
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
