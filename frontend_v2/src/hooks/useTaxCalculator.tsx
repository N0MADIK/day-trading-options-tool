import { useMemo } from 'react';
import { Tables } from '@/integrations/supabase/types';

type Holding = Tables<'holdings'>;
type Transaction = Tables<'transactions'>;

export interface TaxLot {
  symbol: string;
  quantity: number;
  purchasePrice: number;
  purchaseDate: Date;
  currentPrice: number;
  gain: number;
  gainPercent: number;
  isLongTerm: boolean; // Held > 1 year
  taxRate: number;
  estimatedTax: number;
}

export interface SaleRecommendation {
  holding: Holding;
  taxLots: TaxLot[];
  quantityToSell: number;
  proceedsNeeded: number;
  totalProceeds: number;
  totalGain: number;
  estimatedTax: number;
  netProceeds: number;
  isLongTerm: boolean;
}

export interface TradeAnalysis {
  tradeCost: number;
  availableCash: number;
  shortfall: number;
  recommendations: SaleRecommendation[];
  totalProceeds: number;
  totalTax: number;
  netAfterTax: number;
  canAffordTrade: boolean;
}

// Tax rates (simplified for 2024)
const SHORT_TERM_RATE = 0.32; // Ordinary income rate (varies by bracket)
const LONG_TERM_RATE = 0.15; // Capital gains rate (0%, 15%, or 20% depending on income)

export function useTaxCalculator(
  holdings: Holding[],
  transactions: Transaction[],
  userIncomeBracket: 'low' | 'middle' | 'high' = 'middle'
) {
  // Adjust tax rates based on income bracket
  const taxRates = useMemo(() => {
    switch (userIncomeBracket) {
      case 'low':
        return { shortTerm: 0.22, longTerm: 0.0 };
      case 'high':
        return { shortTerm: 0.37, longTerm: 0.20 };
      default:
        return { shortTerm: SHORT_TERM_RATE, longTerm: LONG_TERM_RATE };
    }
  }, [userIncomeBracket]);

  // Build tax lots from transaction history
  const buildTaxLots = (holding: Holding): TaxLot[] => {
    const buyTransactions = transactions.filter(
      t => t.symbol === holding.symbol && 
      (t.transaction_type === 'buy' || t.transaction_type === 'purchase')
    ).sort((a, b) => new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime());

    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);

    const taxLots: TaxLot[] = [];
    let remainingQuantity = holding.quantity || 0;

    for (const tx of buyTransactions) {
      if (remainingQuantity <= 0) break;

      const lotQuantity = Math.min(tx.quantity || 0, remainingQuantity);
      if (lotQuantity <= 0) continue;

      const purchaseDate = new Date(tx.transaction_date);
      const purchasePrice = tx.price || 0;
      const currentPrice = holding.current_price || 0;
      const gain = (currentPrice - purchasePrice) * lotQuantity;
      const gainPercent = purchasePrice > 0 ? ((currentPrice - purchasePrice) / purchasePrice) * 100 : 0;
      const isLongTerm = purchaseDate < oneYearAgo;
      const taxRate = isLongTerm ? taxRates.longTerm : taxRates.shortTerm;
      const estimatedTax = gain > 0 ? gain * taxRate : 0;

      taxLots.push({
        symbol: holding.symbol,
        quantity: lotQuantity,
        purchasePrice,
        purchaseDate,
        currentPrice,
        gain,
        gainPercent,
        isLongTerm,
        taxRate,
        estimatedTax,
      });

      remainingQuantity -= lotQuantity;
    }

    // If we have remaining quantity without transaction history, assume average cost
    if (remainingQuantity > 0 && holding.average_cost) {
      const purchasePrice = holding.average_cost;
      const currentPrice = holding.current_price || 0;
      const gain = (currentPrice - purchasePrice) * remainingQuantity;
      const gainPercent = purchasePrice > 0 ? ((currentPrice - purchasePrice) / purchasePrice) * 100 : 0;
      // Assume long-term if no transaction data
      const isLongTerm = true;
      const taxRate = taxRates.longTerm;
      const estimatedTax = gain > 0 ? gain * taxRate : 0;

      taxLots.push({
        symbol: holding.symbol,
        quantity: remainingQuantity,
        purchasePrice,
        purchaseDate: new Date(Date.now() - 400 * 24 * 60 * 60 * 1000), // Assume 400 days ago
        currentPrice,
        gain,
        gainPercent,
        isLongTerm,
        taxRate,
        estimatedTax,
      });
    }

    return taxLots;
  };

  // Analyze what needs to be sold to fund a trade
  const analyzeTradeRequirements = (
    tradeCost: number,
    availableCash: number = 0,
    preferLongTerm: boolean = true // Prefer selling long-term holdings (lower tax rate)
  ): TradeAnalysis => {
    const shortfall = Math.max(0, tradeCost - availableCash);
    
    if (shortfall <= 0) {
      return {
        tradeCost,
        availableCash,
        shortfall: 0,
        recommendations: [],
        totalProceeds: 0,
        totalTax: 0,
        netAfterTax: tradeCost,
        canAffordTrade: true,
      };
    }

    // Get all holdings with their tax lots, sorted by tax efficiency
    const holdingsWithLots = holdings
      .filter(h => (h.market_value || 0) > 0)
      .map(h => ({
        holding: h,
        taxLots: buildTaxLots(h),
        marketValue: h.market_value || 0,
      }))
      .sort((a, b) => {
        // Sort by tax efficiency: prefer long-term gains, then losses, then short-term gains
        const aHasLongTerm = a.taxLots.some(l => l.isLongTerm);
        const bHasLongTerm = b.taxLots.some(l => l.isLongTerm);
        const aHasLoss = a.taxLots.some(l => l.gain < 0);
        const bHasLoss = b.taxLots.some(l => l.gain < 0);

        if (preferLongTerm) {
          if (aHasLoss && !bHasLoss) return -1;
          if (!aHasLoss && bHasLoss) return 1;
          if (aHasLongTerm && !bHasLongTerm) return -1;
          if (!aHasLongTerm && bHasLongTerm) return 1;
        }

        return 0;
      });

    const recommendations: SaleRecommendation[] = [];
    let remainingShortfall = shortfall;
    let totalProceeds = 0;
    let totalTax = 0;

    for (const { holding, taxLots, marketValue } of holdingsWithLots) {
      if (remainingShortfall <= 0) break;

      const proceedsNeeded = remainingShortfall;
      const maxProceeds = marketValue;
      const actualProceeds = Math.min(proceedsNeeded, maxProceeds);
      const sellRatio = actualProceeds / maxProceeds;

      // Calculate tax on the portion being sold
      let saleGain = 0;
      let saleTax = 0;
      const quantityToSell = (holding.quantity || 0) * sellRatio;

      for (const lot of taxLots) {
        const lotSellQuantity = lot.quantity * sellRatio;
        const lotGain = (lot.currentPrice - lot.purchasePrice) * lotSellQuantity;
        saleGain += lotGain;
        if (lotGain > 0) {
          saleTax += lotGain * lot.taxRate;
        }
      }

      const netProceeds = actualProceeds - saleTax;
      const isLongTerm = taxLots.every(l => l.isLongTerm);

      recommendations.push({
        holding,
        taxLots,
        quantityToSell,
        proceedsNeeded,
        totalProceeds: actualProceeds,
        totalGain: saleGain,
        estimatedTax: saleTax,
        netProceeds,
        isLongTerm,
      });

      totalProceeds += actualProceeds;
      totalTax += saleTax;
      remainingShortfall -= netProceeds;
    }

    return {
      tradeCost,
      availableCash,
      shortfall,
      recommendations,
      totalProceeds,
      totalTax,
      netAfterTax: availableCash + totalProceeds - totalTax,
      canAffordTrade: remainingShortfall <= 0,
    };
  };

  // Get summary of holdings with tax implications
  const getHoldingsSummary = () => {
    return holdings.map(h => ({
      holding: h,
      taxLots: buildTaxLots(h),
      totalUnrealizedGain: h.unrealized_pnl || 0,
      hasLongTermLots: buildTaxLots(h).some(l => l.isLongTerm),
      hasShortTermLots: buildTaxLots(h).some(l => !l.isLongTerm),
    }));
  };

  return {
    analyzeTradeRequirements,
    getHoldingsSummary,
    taxRates,
    buildTaxLots,
  };
}
