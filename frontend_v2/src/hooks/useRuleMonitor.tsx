import { useState, useEffect, useRef, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { toast } from 'sonner';

export interface IndicatorValue {
  indicatorId: string;
  indicatorName: string;
  indicatorType: string;
  value: number;
  timestamp: Date;
}

export interface TradeRuleCondition {
  id: string;
  indicatorId: string;
  indicatorName: string;
  indicatorType: string;
  operator: 'crosses_above' | 'crosses_below' | 'greater_than' | 'less_than' | 'equals' | 'between';
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
  action: 'buy' | 'sell' | 'alert_only';
  orderType: 'market' | 'limit' | 'stop_limit';
  quantity: number;
  limitPrice?: number;
  stopPrice?: number;
  notifyEmail: boolean;
  notifyPush: boolean;
}

export interface RuleTriggerEvent {
  ruleId: string;
  ruleName: string;
  symbol: string;
  action: string;
  triggeredAt: Date;
  indicatorValues: IndicatorValue[];
  message: string;
}

interface UseRuleMonitorOptions {
  rules: TradeRule[];
  pollingInterval?: number; // in ms, default 30000 (30 seconds)
  onRuleTriggered?: (event: RuleTriggerEvent) => void;
}

// Calculate SMA from price data
const calculateSMA = (prices: number[], period: number): number | null => {
  if (prices.length < period) return null;
  const slice = prices.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
};

// Calculate EMA from price data
const calculateEMA = (prices: number[], period: number): number | null => {
  if (prices.length < period) return null;
  const multiplier = 2 / (period + 1);
  let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < prices.length; i++) {
    ema = (prices[i] - ema) * multiplier + ema;
  }
  return ema;
};

// Calculate RSI from price data
const calculateRSI = (prices: number[], period: number): number | null => {
  if (prices.length < period + 1) return null;
  
  const changes = [];
  for (let i = 1; i < prices.length; i++) {
    changes.push(prices[i] - prices[i - 1]);
  }
  
  const gains = changes.map(c => c > 0 ? c : 0);
  const losses = changes.map(c => c < 0 ? Math.abs(c) : 0);
  
  const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period;
  const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period;
  
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
};

// Calculate indicator value based on type
const calculateIndicatorValue = (
  indicatorId: string,
  indicatorType: string,
  prices: number[],
  params: Record<string, number>
): number | null => {
  switch (indicatorType) {
    case 'sma':
      return calculateSMA(prices, params.period || 20);
    case 'ema':
      return calculateEMA(prices, params.period || 12);
    case 'rsi':
      return calculateRSI(prices, params.period || 14);
    case 'macd':
      const fast = calculateEMA(prices, params.fastPeriod || 12);
      const slow = calculateEMA(prices, params.slowPeriod || 26);
      if (fast === null || slow === null) return null;
      return fast - slow;
    default:
      return null;
  }
};

// Evaluate a single condition
const evaluateCondition = (
  condition: TradeRuleCondition,
  currentValue: number,
  previousValue: number | null
): boolean => {
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

export function useRuleMonitor({ rules, pollingInterval = 30000, onRuleTriggered }: UseRuleMonitorOptions) {
  const { user } = useAuth();
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [triggeredRules, setTriggeredRules] = useState<RuleTriggerEvent[]>([]);
  const [indicatorValues, setIndicatorValues] = useState<Map<string, IndicatorValue[]>>(new Map());
  
  const previousValues = useRef<Map<string, Map<string, number>>>(new Map());
  const priceHistory = useRef<Map<string, number[]>>(new Map());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch current price for a symbol
  const fetchPrice = useCallback(async (symbol: string): Promise<number | null> => {
    try {
      const { data, error } = await supabase.functions.invoke('market-data', {
        body: { action: 'quote', symbol, provider: 'yfinance' },
      });

      if (error) throw error;
      if (data?.quote?.price) {
        return data.quote.price;
      }
      return null;
    } catch (err) {
      console.error(`Error fetching price for ${symbol}:`, err);
      return null;
    }
  }, []);

  // Send notification when rule triggers
  const sendNotification = useCallback(async (event: RuleTriggerEvent, rule: TradeRule) => {
    // Browser push notification
    if (rule.notifyPush && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(`Trade Rule Triggered: ${rule.name}`, {
        body: event.message,
        icon: '/favicon.ico',
      });
    }

    // Email notification
    if (rule.notifyEmail && user?.email) {
      try {
        await supabase.functions.invoke('send-trade-alert', {
          body: {
            to: user.email,
            ruleName: rule.name,
            symbol: rule.symbol,
            action: rule.action,
            message: event.message,
            indicatorValues: event.indicatorValues,
          },
        });
      } catch (err) {
        console.error('Error sending email notification:', err);
      }
    }
  }, [user]);

  // Evaluate all rules for a symbol
  const evaluateRules = useCallback(async (symbol: string) => {
    const symbolRules = rules.filter(r => r.enabled && r.symbol === symbol);
    if (symbolRules.length === 0) return;

    const price = await fetchPrice(symbol);
    if (price === null) return;

    // Update price history
    const history = priceHistory.current.get(symbol) || [];
    history.push(price);
    if (history.length > 200) history.shift(); // Keep last 200 prices
    priceHistory.current.set(symbol, history);

    // Get previous indicator values for this symbol
    const prevSymbolValues = previousValues.current.get(symbol) || new Map();
    const newSymbolValues = new Map<string, number>();
    const currentIndicatorValues: IndicatorValue[] = [];

    // Calculate all indicator values
    const indicatorParams: Record<string, Record<string, number>> = {
      'sma-20': { period: 20 },
      'sma-50': { period: 50 },
      'sma-200': { period: 200 },
      'ema-12': { period: 12 },
      'ema-26': { period: 26 },
      'rsi-14': { period: 14 },
      'macd': { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    };

    for (const rule of symbolRules) {
      for (const condition of rule.conditions) {
        const params = indicatorParams[condition.indicatorId] || { period: 20 };
        const value = calculateIndicatorValue(
          condition.indicatorId,
          condition.indicatorType,
          history,
          params
        );

        if (value !== null) {
          newSymbolValues.set(condition.indicatorId, value);
          currentIndicatorValues.push({
            indicatorId: condition.indicatorId,
            indicatorName: condition.indicatorName,
            indicatorType: condition.indicatorType,
            value,
            timestamp: new Date(),
          });
        }
      }
    }

    // Evaluate each rule
    for (const rule of symbolRules) {
      const conditionResults: boolean[] = [];

      for (const condition of rule.conditions) {
        const currentValue = newSymbolValues.get(condition.indicatorId);
        const previousValue = prevSymbolValues.get(condition.indicatorId) || null;

        if (currentValue !== undefined) {
          const result = evaluateCondition(condition, currentValue, previousValue);
          conditionResults.push(result);
        }
      }

      // Check if rule is triggered based on logic
      let isTriggered = false;
      if (conditionResults.length > 0) {
        if (rule.conditionLogic === 'and') {
          isTriggered = conditionResults.every(r => r);
        } else {
          isTriggered = conditionResults.some(r => r);
        }
      }

      if (isTriggered) {
        const event: RuleTriggerEvent = {
          ruleId: rule.id,
          ruleName: rule.name,
          symbol: rule.symbol,
          action: rule.action,
          triggeredAt: new Date(),
          indicatorValues: currentIndicatorValues,
          message: `Rule "${rule.name}" triggered for ${rule.symbol}. Action: ${rule.action.toUpperCase()}`,
        };

        setTriggeredRules(prev => [event, ...prev].slice(0, 50)); // Keep last 50
        onRuleTriggered?.(event);
        sendNotification(event, rule);
        
        toast.success(`Trade Rule Triggered: ${rule.name}`, {
          description: event.message,
        });
      }
    }

    // Update previous values
    previousValues.current.set(symbol, newSymbolValues);
    setIndicatorValues(prev => new Map(prev).set(symbol, currentIndicatorValues));
    setLastCheck(new Date());
  }, [rules, fetchPrice, onRuleTriggered, sendNotification]);

  // Start monitoring
  const startMonitoring = useCallback(() => {
    if (intervalRef.current) return;

    setIsMonitoring(true);
    
    // Get unique symbols from enabled rules
    const symbols = [...new Set(rules.filter(r => r.enabled).map(r => r.symbol))];
    
    // Initial check
    symbols.forEach(symbol => evaluateRules(symbol));

    // Set up polling
    intervalRef.current = setInterval(() => {
      symbols.forEach(symbol => evaluateRules(symbol));
    }, pollingInterval);

    toast.success('Rule monitoring started');
  }, [rules, pollingInterval, evaluateRules]);

  // Stop monitoring
  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsMonitoring(false);
    toast.info('Rule monitoring stopped');
  }, []);

  // Request notification permission
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Update monitoring when rules change
  useEffect(() => {
    if (isMonitoring) {
      stopMonitoring();
      startMonitoring();
    }
  }, [rules]);

  return {
    isMonitoring,
    lastCheck,
    triggeredRules,
    indicatorValues,
    startMonitoring,
    stopMonitoring,
    requestNotificationPermission,
  };
}
