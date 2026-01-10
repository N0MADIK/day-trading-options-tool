import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { format } from 'date-fns';

interface OptionContract {
  ticker: string;
  strike: number;
  expiration: string;
  type: 'call' | 'put';
  bid: number;
  ask: number;
  lastPrice: number;
  volume: number;
  openInterest: number;
  impliedVolatility: number;
}

interface OptionsChain {
  symbol: string;
  expirations: string[];
  chain: Record<string, { calls: OptionContract[]; puts: OptionContract[] }>;
  underlyingPrice?: number;
  provider: string;
}

interface OptionsChainViewerProps {
  symbol: string;
  provider: string;
  credentials?: Record<string, string>;
  onSelectOption?: (option: OptionContract) => void;
  underlyingPrice?: number;
}

export function OptionsChainViewer({
  symbol,
  provider,
  credentials,
  onSelectOption,
  underlyingPrice = 0,
}: OptionsChainViewerProps) {
  const [chain, setChain] = useState<OptionsChain | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedExpiration, setSelectedExpiration] = useState<string>('');
  const [optionType, setOptionType] = useState<'call' | 'put'>('call');

  useEffect(() => {
    if (symbol && symbol.length >= 1) {
      fetchOptionsChain();
    }
  }, [symbol, provider]);

  const fetchOptionsChain = async () => {
    setLoading(true);
    setError(null);

    try {
      const { data, error: fetchError } = await supabase.functions.invoke('market-data', {
        body: {
          action: 'options_chain',
          symbol,
          provider,
          credentials,
        },
      });

      if (fetchError) throw fetchError;
      if (data?.error) throw new Error(data.error);

      setChain(data.chain);
      if (data.chain?.expirations?.length > 0 && !selectedExpiration) {
        setSelectedExpiration(data.chain.expirations[0]);
      }
    } catch (err: unknown) {
      console.error('Error fetching options chain:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch options chain');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
    }).format(value);
  };

  const getMoneyness = (strike: number, type: 'call' | 'put') => {
    if (!underlyingPrice) return 'unknown';
    if (type === 'call') {
      if (strike < underlyingPrice) return 'itm';
      if (strike > underlyingPrice) return 'otm';
      return 'atm';
    } else {
      if (strike > underlyingPrice) return 'itm';
      if (strike < underlyingPrice) return 'otm';
      return 'atm';
    }
  };

  const getMoneynessBadge = (strike: number, type: 'call' | 'put') => {
    const moneyness = getMoneyness(strike, type);
    switch (moneyness) {
      case 'itm':
        return <Badge variant="default" className="text-xs">ITM</Badge>;
      case 'otm':
        return <Badge variant="secondary" className="text-xs">OTM</Badge>;
      case 'atm':
        return <Badge variant="outline" className="text-xs">ATM</Badge>;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Card className="border-border bg-card">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span className="text-muted-foreground">Loading options chain...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-border bg-card">
        <CardContent className="p-6 text-center">
          <p className="text-destructive mb-2">{error}</p>
          <Button onClick={fetchOptionsChain} variant="outline" size="sm">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!chain) {
    return (
      <Card className="border-border bg-card">
        <CardContent className="p-6 text-center text-muted-foreground">
          Enter a symbol to view options chain
        </CardContent>
      </Card>
    );
  }

  const currentChain = selectedExpiration ? chain.chain[selectedExpiration] : null;
  const options = currentChain ? (optionType === 'call' ? currentChain.calls : currentChain.puts) : [];

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Options Chain: {symbol}</span>
          <Badge variant="outline">{chain.provider}</Badge>
        </CardTitle>
        <CardDescription>
          {underlyingPrice > 0 && `Underlying: ${formatCurrency(underlyingPrice)} • `}
          {chain.expirations.length} expiration dates available
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex gap-4 items-center">
          <div className="flex-1">
            <Select value={selectedExpiration} onValueChange={setSelectedExpiration}>
              <SelectTrigger>
                <SelectValue placeholder="Select expiration" />
              </SelectTrigger>
              <SelectContent>
                {chain.expirations.map((exp) => (
                  <SelectItem key={exp} value={exp}>
                    {format(new Date(exp + 'T00:00:00'), 'MMM d, yyyy')} ({getDaysToExpiration(exp)} days)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Tabs value={optionType} onValueChange={(v) => setOptionType(v as 'call' | 'put')}>
            <TabsList>
              <TabsTrigger value="call" className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4" />
                Calls
              </TabsTrigger>
              <TabsTrigger value="put" className="flex items-center gap-1">
                <TrendingDown className="h-4 w-4" />
                Puts
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <Button onClick={fetchOptionsChain} variant="outline" size="sm">
            Refresh
          </Button>
        </div>

        {/* Options Table */}
        <ScrollArea className="h-[400px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Strike</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Bid</TableHead>
                <TableHead className="text-right">Ask</TableHead>
                <TableHead className="text-right">Last</TableHead>
                <TableHead className="text-right">Volume</TableHead>
                <TableHead className="text-right">Open Int.</TableHead>
                <TableHead className="text-right">IV</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {options.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                    No options available for this expiration
                  </TableCell>
                </TableRow>
              ) : (
                options.map((option) => (
                  <TableRow
                    key={option.ticker}
                    className={`cursor-pointer hover:bg-secondary/50 transition-colors ${
                      getMoneyness(option.strike, option.type) === 'itm' ? 'bg-primary/5' : ''
                    }`}
                    onClick={() => onSelectOption?.(option)}
                  >
                    <TableCell className="font-medium">{formatCurrency(option.strike)}</TableCell>
                    <TableCell>{getMoneynessBadge(option.strike, option.type)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(option.bid)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(option.ask)}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(option.lastPrice)}</TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {option.volume.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {option.openInterest.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {option.impliedVolatility > 0 ? formatPercent(option.impliedVolatility) : '—'}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectOption?.(option);
                        }}
                      >
                        Select
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </ScrollArea>

        {/* Legend */}
        <div className="flex gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Badge variant="default" className="text-xs">ITM</Badge>
            <span>In The Money</span>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="outline" className="text-xs">ATM</Badge>
            <span>At The Money</span>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="secondary" className="text-xs">OTM</Badge>
            <span>Out of The Money</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getDaysToExpiration(expirationDate: string): number {
  const today = new Date();
  const expDate = new Date(expirationDate + 'T00:00:00');
  const diffTime = expDate.getTime() - today.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}
