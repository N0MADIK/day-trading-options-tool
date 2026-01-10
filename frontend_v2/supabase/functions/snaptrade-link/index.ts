import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createHmac } from "https://deno.land/std@0.168.0/node/crypto.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const SNAPTRADE_BASE_URL = 'https://api.snaptrade.com/api/v1';

function generateSignature(consumerKey: string, timestamp: string, path: string): string {
  const message = `${timestamp}${path}`;
  const hmac = createHmac('sha256', consumerKey);
  hmac.update(message);
  return hmac.digest('base64');
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { action, user_id, user_secret, account_id } = await req.json();
    const clientId = Deno.env.get('SNAPTRADE_CLIENT_ID');
    const consumerKey = Deno.env.get('SNAPTRADE_CONSUMER_KEY');

    if (!clientId || !consumerKey) {
      console.error('SnapTrade credentials not configured');
      throw new Error('SnapTrade credentials not configured');
    }

    console.log(`SnapTrade action: ${action}`);

    const timestamp = Math.floor(Date.now() / 1000).toString();

    // Register User
    if (action === 'register_user') {
      const path = '/snapTrade/registerUser';
      const signature = generateSignature(consumerKey, timestamp, path);

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
        body: JSON.stringify({ userId: user_id }),
      });

      const data = await response.json();
      console.log('Register user response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to register user');
      }

      return new Response(JSON.stringify({ 
        user_id: data.userId,
        user_secret: data.userSecret 
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Connection Portal URL
    if (action === 'get_login_link') {
      const path = `/snapTrade/login`;
      const signature = generateSignature(consumerKey, timestamp, path);

      const queryParams = new URLSearchParams({
        userId: user_id,
        userSecret: user_secret,
        ...(account_id && { broker: account_id }),
      });

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
      });

      const data = await response.json();
      console.log('Login link response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get login link');
      }

      return new Response(JSON.stringify({ redirect_uri: data.redirectURI }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // List User Connections
    if (action === 'list_connections') {
      const path = `/authorizations`;
      const signature = generateSignature(consumerKey, timestamp, path);

      const queryParams = new URLSearchParams({
        userId: user_id,
        userSecret: user_secret,
      });

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
      });

      const data = await response.json();
      console.log('Connections response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to list connections');
      }

      return new Response(JSON.stringify({ connections: data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Accounts
    if (action === 'get_accounts') {
      const path = `/accounts`;
      const signature = generateSignature(consumerKey, timestamp, path);

      const queryParams = new URLSearchParams({
        userId: user_id,
        userSecret: user_secret,
      });

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
      });

      const data = await response.json();
      console.log('Accounts response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get accounts');
      }

      return new Response(JSON.stringify({ accounts: data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Holdings
    if (action === 'get_holdings') {
      const path = `/holdings`;
      const signature = generateSignature(consumerKey, timestamp, path);

      const queryParams = new URLSearchParams({
        userId: user_id,
        userSecret: user_secret,
        ...(account_id && { accounts: account_id }),
      });

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
      });

      const data = await response.json();
      console.log('Holdings response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get holdings');
      }

      return new Response(JSON.stringify({ holdings: data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Account Balances
    if (action === 'get_balances') {
      const path = `/accounts/${account_id}/balances`;
      const signature = generateSignature(consumerKey, timestamp, path);

      const queryParams = new URLSearchParams({
        userId: user_id,
        userSecret: user_secret,
      });

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
      });

      const data = await response.json();
      console.log('Balances response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get balances');
      }

      return new Response(JSON.stringify({ balances: data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Transaction History
    if (action === 'get_activities') {
      const path = `/activities`;
      const signature = generateSignature(consumerKey, timestamp, path);

      const queryParams = new URLSearchParams({
        userId: user_id,
        userSecret: user_secret,
        ...(account_id && { accounts: account_id }),
      });

      const response = await fetch(`${SNAPTRADE_BASE_URL}${path}?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Timestamp': timestamp,
          'clientId': clientId,
          'Signature': signature,
        },
      });

      const data = await response.json();
      console.log('Activities response:', JSON.stringify(data));

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get activities');
      }

      return new Response(JSON.stringify({ activities: data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    throw new Error(`Unknown action: ${action}`);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    console.error('SnapTrade function error:', error);
    return new Response(JSON.stringify({ error: errorMessage }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
