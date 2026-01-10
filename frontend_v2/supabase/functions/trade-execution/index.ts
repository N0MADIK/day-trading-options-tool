import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Alpaca API endpoints
const ALPACA_PAPER_URL = "https://paper-api.alpaca.markets";
const ALPACA_LIVE_URL = "https://api.alpaca.markets";

interface OrderRequest {
  symbol: string;
  quantity: number;
  side: "buy" | "sell";
  type: "market" | "limit" | "stop" | "stop_limit";
  time_in_force: "day" | "gtc" | "ioc" | "fok";
  limit_price?: number;
  stop_price?: number;
  take_profit?: number;
  stop_loss?: number;
  broker: "alpaca" | "interactive_brokers";
  credentials: {
    api_key: string;
    api_secret: string;
  };
  paper_trading?: boolean;
}

interface OrderPreviewRequest {
  symbol: string;
  quantity: number;
  side: "buy" | "sell";
  type: "market" | "limit";
  limit_price?: number;
  broker: "alpaca" | "interactive_brokers";
  credentials: {
    api_key: string;
    api_secret: string;
  };
}

async function getAlpacaAccount(apiKey: string, apiSecret: string, paperTrading = true) {
  const baseUrl = paperTrading ? ALPACA_PAPER_URL : ALPACA_LIVE_URL;
  
  const response = await fetch(`${baseUrl}/v2/account`, {
    headers: {
      "APCA-API-KEY-ID": apiKey,
      "APCA-API-SECRET-KEY": apiSecret,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Alpaca account error:", errorText);
    throw new Error(`Failed to get account: ${response.status}`);
  }

  return await response.json();
}

async function previewAlpacaOrder(params: OrderPreviewRequest, paperTrading = true) {
  const { symbol, quantity, side, type, limit_price, credentials } = params;
  
  // Get current quote for estimated fill price
  const quoteResponse = await fetch(
    `https://data.alpaca.markets/v2/stocks/${symbol}/quotes/latest`,
    {
      headers: {
        "APCA-API-KEY-ID": credentials.api_key,
        "APCA-API-SECRET-KEY": credentials.api_secret,
      },
    }
  );

  let estimatedPrice = limit_price || 0;
  if (quoteResponse.ok) {
    const quoteData = await quoteResponse.json();
    if (type === "market") {
      estimatedPrice = side === "buy" ? quoteData.quote?.ap : quoteData.quote?.bp;
    }
  }

  // Get account for buying power check
  const account = await getAlpacaAccount(credentials.api_key, credentials.api_secret, paperTrading);
  
  const estimatedTotal = estimatedPrice * quantity;
  const buyingPower = parseFloat(account.buying_power);
  const canExecute = side === "sell" || estimatedTotal <= buyingPower;

  // Estimate commission (Alpaca is commission-free for stocks)
  const commission = 0;
  
  // Calculate fees (SEC and FINRA fees for sells)
  let fees = 0;
  if (side === "sell") {
    // SEC fee: $8 per $1,000,000 of principal
    fees += (estimatedTotal / 1000000) * 8;
    // FINRA TAF: $0.000119 per share, max $5.95
    fees += Math.min(quantity * 0.000119, 5.95);
  }

  return {
    symbol,
    side,
    quantity,
    type,
    limit_price: limit_price || null,
    estimated_price: estimatedPrice,
    estimated_total: estimatedTotal,
    commission,
    fees: Math.round(fees * 100) / 100,
    total_cost: estimatedTotal + commission + fees,
    buying_power: buyingPower,
    can_execute: canExecute,
    account_status: account.status,
    day_trade_count: account.daytrade_count,
    pattern_day_trader: account.pattern_day_trader,
  };
}

async function submitAlpacaOrder(params: OrderRequest) {
  const { 
    symbol, 
    quantity, 
    side, 
    type, 
    time_in_force, 
    limit_price, 
    stop_price,
    take_profit,
    stop_loss,
    credentials,
    paper_trading = true
  } = params;

  const baseUrl = paper_trading ? ALPACA_PAPER_URL : ALPACA_LIVE_URL;

  // Build order body
  const orderBody: any = {
    symbol,
    qty: quantity.toString(),
    side,
    type,
    time_in_force,
  };

  if (type === "limit" || type === "stop_limit") {
    orderBody.limit_price = limit_price?.toString();
  }

  if (type === "stop" || type === "stop_limit") {
    orderBody.stop_price = stop_price?.toString();
  }

  // Add bracket order legs if take profit or stop loss specified
  if (take_profit || stop_loss) {
    orderBody.order_class = "bracket";
    
    if (take_profit) {
      orderBody.take_profit = {
        limit_price: take_profit.toString(),
      };
    }
    
    if (stop_loss) {
      orderBody.stop_loss = {
        stop_price: stop_loss.toString(),
      };
    }
  }

  console.log("Submitting Alpaca order:", JSON.stringify(orderBody));

  const response = await fetch(`${baseUrl}/v2/orders`, {
    method: "POST",
    headers: {
      "APCA-API-KEY-ID": credentials.api_key,
      "APCA-API-SECRET-KEY": credentials.api_secret,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(orderBody),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Alpaca order error:", errorText);
    throw new Error(`Order failed: ${errorText}`);
  }

  const order = await response.json();
  
  return {
    order_id: order.id,
    client_order_id: order.client_order_id,
    symbol: order.symbol,
    side: order.side,
    quantity: parseFloat(order.qty),
    filled_quantity: parseFloat(order.filled_qty || "0"),
    type: order.type,
    status: order.status,
    limit_price: order.limit_price ? parseFloat(order.limit_price) : null,
    stop_price: order.stop_price ? parseFloat(order.stop_price) : null,
    filled_avg_price: order.filled_avg_price ? parseFloat(order.filled_avg_price) : null,
    created_at: order.created_at,
    submitted_at: order.submitted_at,
    filled_at: order.filled_at,
    legs: order.legs,
    broker: "alpaca",
    paper_trading,
  };
}

async function getAlpacaOrders(credentials: { api_key: string; api_secret: string }, paperTrading = true, status = "all") {
  const baseUrl = paperTrading ? ALPACA_PAPER_URL : ALPACA_LIVE_URL;
  
  const response = await fetch(`${baseUrl}/v2/orders?status=${status}&limit=50`, {
    headers: {
      "APCA-API-KEY-ID": credentials.api_key,
      "APCA-API-SECRET-KEY": credentials.api_secret,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Alpaca orders error:", errorText);
    throw new Error(`Failed to get orders: ${response.status}`);
  }

  const orders = await response.json();
  
  return orders.map((order: any) => ({
    order_id: order.id,
    client_order_id: order.client_order_id,
    symbol: order.symbol,
    side: order.side,
    quantity: parseFloat(order.qty),
    filled_quantity: parseFloat(order.filled_qty || "0"),
    type: order.type,
    status: order.status,
    limit_price: order.limit_price ? parseFloat(order.limit_price) : null,
    stop_price: order.stop_price ? parseFloat(order.stop_price) : null,
    filled_avg_price: order.filled_avg_price ? parseFloat(order.filled_avg_price) : null,
    created_at: order.created_at,
    submitted_at: order.submitted_at,
    filled_at: order.filled_at,
  }));
}

async function cancelAlpacaOrder(orderId: string, credentials: { api_key: string; api_secret: string }, paperTrading = true) {
  const baseUrl = paperTrading ? ALPACA_PAPER_URL : ALPACA_LIVE_URL;
  
  const response = await fetch(`${baseUrl}/v2/orders/${orderId}`, {
    method: "DELETE",
    headers: {
      "APCA-API-KEY-ID": credentials.api_key,
      "APCA-API-SECRET-KEY": credentials.api_secret,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Alpaca cancel error:", errorText);
    throw new Error(`Failed to cancel order: ${response.status}`);
  }

  return { success: true, order_id: orderId };
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { action, ...params } = await req.json();
    console.log(`Trade execution action: ${action}`);

    if (action === "preview") {
      const preview = await previewAlpacaOrder(params as OrderPreviewRequest);
      return new Response(
        JSON.stringify({ preview }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (action === "submit") {
      const order = await submitAlpacaOrder(params as OrderRequest);
      return new Response(
        JSON.stringify({ order }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (action === "get_orders") {
      const { credentials, paper_trading, status } = params;
      const orders = await getAlpacaOrders(credentials, paper_trading, status);
      return new Response(
        JSON.stringify({ orders }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (action === "cancel") {
      const { order_id, credentials, paper_trading } = params;
      const result = await cancelAlpacaOrder(order_id, credentials, paper_trading);
      return new Response(
        JSON.stringify(result),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (action === "get_account") {
      const { credentials, paper_trading } = params;
      const account = await getAlpacaAccount(credentials.api_key, credentials.api_secret, paper_trading);
      return new Response(
        JSON.stringify({ account }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({ error: "Unknown action" }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: unknown) {
    console.error("Trade execution error:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
