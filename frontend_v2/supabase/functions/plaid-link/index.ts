import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const PLAID_ENV = Deno.env.get('PLAID_ENV') || 'sandbox';
const PLAID_BASE_URL = PLAID_ENV === 'production' 
  ? 'https://production.plaid.com'
  : PLAID_ENV === 'development'
    ? 'https://development.plaid.com'
    : 'https://sandbox.plaid.com';

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { action, user_id, public_token, access_token, institution_id } = await req.json();
    const clientId = Deno.env.get('PLAID_CLIENT_ID');
    const secret = Deno.env.get('PLAID_SECRET');

    if (!clientId || !secret) {
      console.error('Plaid credentials not configured');
      throw new Error('Plaid credentials not configured');
    }

    console.log(`Plaid action: ${action}, env: ${PLAID_ENV}`);

    // Create Link Token
    if (action === 'create_link_token') {
      // Get the origin from request headers for redirect
      const origin = req.headers.get('origin') || 'http://localhost:5173';
      
      const response = await fetch(`${PLAID_BASE_URL}/link/token/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          secret: secret,
          user: { client_user_id: user_id },
          client_name: 'WealthOS',
          products: ['auth', 'transactions', 'investments', 'liabilities'],
          country_codes: ['US'],
          language: 'en',
          redirect_uri: undefined, // Not needed for desktop/web Link
        }),
      });

      const data = await response.json();
      console.log('Link token response:', JSON.stringify(data));
      
      if (data.error_code) {
        throw new Error(data.error_message || 'Failed to create link token');
      }

      return new Response(JSON.stringify({ link_token: data.link_token }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Exchange Public Token for Access Token
    if (action === 'exchange_token') {
      const response = await fetch(`${PLAID_BASE_URL}/item/public_token/exchange`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          secret: secret,
          public_token: public_token,
        }),
      });

      const data = await response.json();
      console.log('Token exchange response:', JSON.stringify(data));
      
      if (data.error_code) {
        throw new Error(data.error_message || 'Failed to exchange token');
      }

      return new Response(JSON.stringify({ 
        access_token: data.access_token,
        item_id: data.item_id 
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Accounts
    if (action === 'get_accounts') {
      const response = await fetch(`${PLAID_BASE_URL}/accounts/get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          secret: secret,
          access_token: access_token,
        }),
      });

      const data = await response.json();
      console.log('Accounts response:', JSON.stringify(data));
      
      if (data.error_code) {
        throw new Error(data.error_message || 'Failed to get accounts');
      }

      return new Response(JSON.stringify({ accounts: data.accounts }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Transactions
    if (action === 'get_transactions') {
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      const response = await fetch(`${PLAID_BASE_URL}/transactions/get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          secret: secret,
          access_token: access_token,
          start_date: startDate,
          end_date: endDate,
        }),
      });

      const data = await response.json();
      console.log('Transactions response:', JSON.stringify(data));
      
      if (data.error_code) {
        throw new Error(data.error_message || 'Failed to get transactions');
      }

      return new Response(JSON.stringify({ transactions: data.transactions }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Investment Holdings
    if (action === 'get_holdings') {
      const response = await fetch(`${PLAID_BASE_URL}/investments/holdings/get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          secret: secret,
          access_token: access_token,
        }),
      });

      const data = await response.json();
      console.log('Holdings response:', JSON.stringify(data));
      
      if (data.error_code) {
        throw new Error(data.error_message || 'Failed to get holdings');
      }

      return new Response(JSON.stringify({ 
        holdings: data.holdings,
        securities: data.securities,
        accounts: data.accounts 
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Liabilities (Credit Cards)
    if (action === 'get_liabilities') {
      const response = await fetch(`${PLAID_BASE_URL}/liabilities/get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          secret: secret,
          access_token: access_token,
        }),
      });

      const data = await response.json();
      console.log('Liabilities response:', JSON.stringify(data));
      
      if (data.error_code) {
        throw new Error(data.error_message || 'Failed to get liabilities');
      }

      return new Response(JSON.stringify({ liabilities: data.liabilities }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    throw new Error(`Unknown action: ${action}`);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    console.error('Plaid function error:', error);
    return new Response(JSON.stringify({ error: errorMessage }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
