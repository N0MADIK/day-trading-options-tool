import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface QuoteRequest {
  symbol: string;
  provider: string;
  credentials?: {
    api_key?: string;
    api_secret?: string;
  };
}

interface OptionsChainRequest {
  symbol: string;
  provider: string;
  expiration_date?: string;
  credentials?: {
    api_key?: string;
    api_secret?: string;
  };
}

// Alpaca API endpoints
const ALPACA_PAPER_URL = "https://paper-api.alpaca.markets";
const ALPACA_DATA_URL = "https://data.alpaca.markets";

// Polygon API endpoint
const POLYGON_URL = "https://api.polygon.io";

async function fetchAlpacaQuote(symbol: string, apiKey: string, apiSecret: string) {
  console.log(`Fetching Alpaca quote for ${symbol}`);
  
  const response = await fetch(
    `${ALPACA_DATA_URL}/v2/stocks/${symbol}/quotes/latest`,
    {
      headers: {
        "APCA-API-KEY-ID": apiKey,
        "APCA-API-SECRET-KEY": apiSecret,
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Alpaca quote error:", errorText);
    throw new Error(`Alpaca API error: ${response.status}`);
  }

  const data = await response.json();
  
  // Also fetch the latest trade for price
  const tradeResponse = await fetch(
    `${ALPACA_DATA_URL}/v2/stocks/${symbol}/trades/latest`,
    {
      headers: {
        "APCA-API-KEY-ID": apiKey,
        "APCA-API-SECRET-KEY": apiSecret,
      },
    }
  );

  let tradeData = null;
  if (tradeResponse.ok) {
    tradeData = await tradeResponse.json();
  }

  // Fetch daily bars for high/low
  const barsResponse = await fetch(
    `${ALPACA_DATA_URL}/v2/stocks/${symbol}/bars/latest?feed=iex`,
    {
      headers: {
        "APCA-API-KEY-ID": apiKey,
        "APCA-API-SECRET-KEY": apiSecret,
      },
    }
  );

  let barsData = null;
  if (barsResponse.ok) {
    barsData = await barsResponse.json();
  }

  const quote = data.quote;
  const trade = tradeData?.trade;
  const bar = barsData?.bar;

  const price = trade?.p || quote?.ap || 0;
  const prevClose = bar?.c || price;

  return {
    symbol: symbol.toUpperCase(),
    price,
    change: price - prevClose,
    changePercent: prevClose ? ((price - prevClose) / prevClose) * 100 : 0,
    bid: quote?.bp || price - 0.01,
    ask: quote?.ap || price + 0.01,
    bidSize: quote?.bs || 0,
    askSize: quote?.as || 0,
    high: bar?.h || price,
    low: bar?.l || price,
    open: bar?.o || price,
    volume: bar?.v || 0,
    lastUpdated: new Date().toISOString(),
    provider: "alpaca",
  };
}

async function fetchPolygonQuote(symbol: string, apiKey: string) {
  console.log(`Fetching Polygon quote for ${symbol}`);
  
  // Get previous day's data for price reference
  const prevDayResponse = await fetch(
    `${POLYGON_URL}/v2/aggs/ticker/${symbol}/prev?apiKey=${apiKey}`
  );

  if (!prevDayResponse.ok) {
    const errorText = await prevDayResponse.text();
    console.error("Polygon prev day error:", errorText);
    throw new Error(`Polygon API error: ${prevDayResponse.status}`);
  }

  const prevDayData = await prevDayResponse.json();
  
  // Get latest quote
  const quoteResponse = await fetch(
    `${POLYGON_URL}/v3/quotes/${symbol}?limit=1&apiKey=${apiKey}`
  );

  let quoteData = null;
  if (quoteResponse.ok) {
    quoteData = await quoteResponse.json();
  }

  const results = prevDayData.results?.[0];
  const latestQuote = quoteData?.results?.[0];

  if (!results) {
    throw new Error("No data found for symbol");
  }

  const price = results.c;
  const prevClose = results.o;

  return {
    symbol: symbol.toUpperCase(),
    price,
    change: price - prevClose,
    changePercent: prevClose ? ((price - prevClose) / prevClose) * 100 : 0,
    bid: latestQuote?.bid_price || price - 0.01,
    ask: latestQuote?.ask_price || price + 0.01,
    bidSize: latestQuote?.bid_size || 0,
    askSize: latestQuote?.ask_size || 0,
    high: results.h,
    low: results.l,
    open: results.o,
    volume: results.v,
    lastUpdated: new Date().toISOString(),
    provider: "polygon",
  };
}

async function fetchPolygonOptionsChain(symbol: string, apiKey: string, expirationDate?: string) {
  console.log(`Fetching Polygon options chain for ${symbol}`);
  
  // First get available expirations
  let expParam = "";
  if (expirationDate) {
    expParam = `&expiration_date=${expirationDate}`;
  } else {
    // Get next 30 days of expirations
    const today = new Date();
    const thirtyDaysOut = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
    expParam = `&expiration_date.gte=${today.toISOString().split('T')[0]}&expiration_date.lte=${thirtyDaysOut.toISOString().split('T')[0]}`;
  }

  const response = await fetch(
    `${POLYGON_URL}/v3/reference/options/contracts?underlying_ticker=${symbol}${expParam}&limit=250&apiKey=${apiKey}`
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Polygon options error:", errorText);
    throw new Error(`Polygon options API error: ${response.status}`);
  }

  const data = await response.json();
  
  // Get quotes for each option contract (limited to first 50 for performance)
  const contracts = data.results?.slice(0, 50) || [];
  
  const optionsWithQuotes = await Promise.all(
    contracts.map(async (contract: any) => {
      try {
        const quoteResponse = await fetch(
          `${POLYGON_URL}/v3/quotes/${contract.ticker}?limit=1&apiKey=${apiKey}`
        );
        
        let quote = null;
        if (quoteResponse.ok) {
          const quoteData = await quoteResponse.json();
          quote = quoteData.results?.[0];
        }

        return {
          ticker: contract.ticker,
          strike: contract.strike_price,
          expiration: contract.expiration_date,
          type: contract.contract_type, // call or put
          bid: quote?.bid_price || 0,
          ask: quote?.ask_price || 0,
          lastPrice: quote?.last_trade?.price || 0,
          volume: 0,
          openInterest: 0,
          impliedVolatility: 0,
        };
      } catch (e) {
        return {
          ticker: contract.ticker,
          strike: contract.strike_price,
          expiration: contract.expiration_date,
          type: contract.contract_type,
          bid: 0,
          ask: 0,
          lastPrice: 0,
          volume: 0,
          openInterest: 0,
          impliedVolatility: 0,
        };
      }
    })
  );

  // Group by expiration and type
  const grouped: Record<string, { calls: any[]; puts: any[] }> = {};
  
  for (const option of optionsWithQuotes) {
    if (!grouped[option.expiration]) {
      grouped[option.expiration] = { calls: [], puts: [] };
    }
    if (option.type === "call") {
      grouped[option.expiration].calls.push(option);
    } else {
      grouped[option.expiration].puts.push(option);
    }
  }

  // Sort by strike price
  for (const exp of Object.keys(grouped)) {
    grouped[exp].calls.sort((a, b) => a.strike - b.strike);
    grouped[exp].puts.sort((a, b) => a.strike - b.strike);
  }

  return {
    symbol: symbol.toUpperCase(),
    expirations: Object.keys(grouped).sort(),
    chain: grouped,
    provider: "polygon",
  };
}

// Mock fallback for when no real API is available
function getMockQuote(symbol: string) {
  const mockPrices: Record<string, number> = {
    'AAPL': 178.50, 'TSLA': 248.50, 'NVDA': 495.20, 'MSFT': 378.90,
    'GOOGL': 141.80, 'AMZN': 178.25, 'META': 485.60, 'SPY': 475.30,
    'QQQ': 405.75, 'VTI': 235.80, 'BND': 72.30, 'AMD': 145.60,
  };

  const basePrice = mockPrices[symbol.toUpperCase()] || (50 + Math.random() * 200);
  const changePercent = (Math.random() - 0.5) * 4;
  const change = basePrice * (changePercent / 100);

  return {
    symbol: symbol.toUpperCase(),
    price: basePrice,
    change,
    changePercent,
    bid: basePrice - 0.01,
    ask: basePrice + 0.01,
    bidSize: Math.floor(Math.random() * 1000),
    askSize: Math.floor(Math.random() * 1000),
    high: basePrice * 1.02,
    low: basePrice * 0.98,
    open: basePrice * 0.995,
    volume: Math.floor(Math.random() * 10000000),
    lastUpdated: new Date().toISOString(),
    provider: "mock",
  };
}

function getMockOptionsChain(symbol: string) {
  const basePrice = 175;
  const expirations = [];
  const chain: Record<string, { calls: any[]; puts: any[] }> = {};

  // Generate 4 weekly expirations
  for (let i = 1; i <= 4; i++) {
    const date = new Date();
    date.setDate(date.getDate() + (i * 7));
    const friday = new Date(date);
    friday.setDate(friday.getDate() + (5 - friday.getDay()) % 7);
    const expStr = friday.toISOString().split('T')[0];
    expirations.push(expStr);

    const calls = [];
    const puts = [];

    // Generate strikes around the current price
    for (let strike = basePrice - 20; strike <= basePrice + 20; strike += 2.5) {
      const timeFactor = i * 0.02;
      const callPrice = Math.max(0.01, basePrice - strike + (Math.random() * 5) + timeFactor * 10);
      const putPrice = Math.max(0.01, strike - basePrice + (Math.random() * 5) + timeFactor * 10);

      calls.push({
        ticker: `O:${symbol}${expStr.replace(/-/g, '')}C${strike.toFixed(0).padStart(8, '0')}`,
        strike,
        expiration: expStr,
        type: "call",
        bid: Math.max(0.01, callPrice - 0.05),
        ask: callPrice + 0.05,
        lastPrice: callPrice,
        volume: Math.floor(Math.random() * 5000),
        openInterest: Math.floor(Math.random() * 10000),
        impliedVolatility: 0.25 + Math.random() * 0.3,
      });

      puts.push({
        ticker: `O:${symbol}${expStr.replace(/-/g, '')}P${strike.toFixed(0).padStart(8, '0')}`,
        strike,
        expiration: expStr,
        type: "put",
        bid: Math.max(0.01, putPrice - 0.05),
        ask: putPrice + 0.05,
        lastPrice: putPrice,
        volume: Math.floor(Math.random() * 5000),
        openInterest: Math.floor(Math.random() * 10000),
        impliedVolatility: 0.25 + Math.random() * 0.3,
      });
    }

    chain[expStr] = { calls, puts };
  }

  return {
    symbol: symbol.toUpperCase(),
    expirations,
    chain,
    underlyingPrice: basePrice,
    provider: "mock",
  };
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { action, ...params } = await req.json();
    console.log(`Market data action: ${action}`, params);

    if (action === "quote") {
      const { symbol, provider, credentials } = params as QuoteRequest;

      if (!symbol) {
        return new Response(
          JSON.stringify({ error: "Symbol is required" }),
          { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      let quote;

      if (provider === "alpaca" && credentials?.api_key && credentials?.api_secret) {
        quote = await fetchAlpacaQuote(symbol, credentials.api_key, credentials.api_secret);
      } else if (provider === "polygon" && credentials?.api_key) {
        quote = await fetchPolygonQuote(symbol, credentials.api_key);
      } else {
        // Fallback to mock data
        quote = getMockQuote(symbol);
      }

      return new Response(
        JSON.stringify({ quote }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (action === "options_chain") {
      const { symbol, provider, expiration_date, credentials } = params as OptionsChainRequest;

      if (!symbol) {
        return new Response(
          JSON.stringify({ error: "Symbol is required" }),
          { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      let chain;

      if (provider === "polygon" && credentials?.api_key) {
        chain = await fetchPolygonOptionsChain(symbol, credentials.api_key, expiration_date);
      } else {
        // Fallback to mock data
        chain = getMockOptionsChain(symbol);
      }

      return new Response(
        JSON.stringify({ chain }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({ error: "Unknown action" }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: unknown) {
    console.error("Market data error:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
