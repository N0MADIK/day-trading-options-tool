import { serve } from "https://deno.land/std@0.190.0/http/server.ts";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface TradeAlertRequest {
  to: string;
  ruleName: string;
  symbol: string;
  action: string;
  message: string;
  indicatorValues?: Array<{
    indicatorName: string;
    value: number;
  }>;
}

const handler = async (req: Request): Promise<Response> => {
  console.log("send-trade-alert function called");

  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    if (!RESEND_API_KEY) {
      throw new Error("RESEND_API_KEY is not configured");
    }

    const { to, ruleName, symbol, action, message, indicatorValues }: TradeAlertRequest = await req.json();

    console.log(`Sending trade alert to ${to} for rule: ${ruleName}`);

    // Build indicator values HTML
    let indicatorHtml = "";
    if (indicatorValues && indicatorValues.length > 0) {
      indicatorHtml = `
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
          <tr style="background-color: #1a1a2e;">
            <th style="padding: 10px; text-align: left; border-bottom: 1px solid #333;">Indicator</th>
            <th style="padding: 10px; text-align: right; border-bottom: 1px solid #333;">Value</th>
          </tr>
          ${indicatorValues.map(iv => `
            <tr>
              <td style="padding: 10px; border-bottom: 1px solid #222;">${iv.indicatorName}</td>
              <td style="padding: 10px; text-align: right; border-bottom: 1px solid #222;">${iv.value.toFixed(2)}</td>
            </tr>
          `).join("")}
        </table>
      `;
    }

    // Determine action color
    const actionColor = action === "buy" ? "#22c55e" : action === "sell" ? "#ef4444" : "#f59e0b";
    const actionLabel = action === "alert_only" ? "ALERT" : action.toUpperCase();

    const emailHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0a0a0f;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <!-- Header -->
          <div style="background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%); border-radius: 12px; padding: 30px; margin-bottom: 20px; border: 1px solid #333;">
            <h1 style="margin: 0 0 10px 0; color: #22c55e; font-size: 24px;">
              🚨 Trade Rule Triggered
            </h1>
            <p style="margin: 0; color: #888; font-size: 14px;">
              Finance Monkey Alert System 🐵
            </p>
          </div>

          <!-- Main Content -->
          <div style="background-color: #16161a; border-radius: 12px; padding: 30px; border: 1px solid #333;">
            <!-- Rule Info -->
            <div style="margin-bottom: 25px;">
              <h2 style="margin: 0 0 15px 0; color: #fff; font-size: 20px;">
                ${ruleName}
              </h2>
              <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <span style="background-color: #1a1a2e; color: #22c55e; padding: 6px 12px; border-radius: 6px; font-family: monospace; font-weight: bold;">
                  ${symbol}
                </span>
                <span style="background-color: ${actionColor}20; color: ${actionColor}; padding: 6px 12px; border-radius: 6px; font-weight: bold;">
                  ${actionLabel}
                </span>
              </div>
            </div>

            <!-- Message -->
            <div style="background-color: #1a1a2e; border-radius: 8px; padding: 20px; margin-bottom: 25px; border-left: 4px solid #22c55e;">
              <p style="margin: 0; color: #ccc; line-height: 1.6;">
                ${message}
              </p>
            </div>

            <!-- Indicator Values -->
            ${indicatorHtml}

            <!-- Timestamp -->
            <p style="margin: 20px 0 0 0; color: #666; font-size: 12px;">
              Triggered at: ${new Date().toLocaleString()}
            </p>
          </div>

          <!-- Footer -->
          <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p style="margin: 0 0 10px 0;">
              This alert was sent by Finance Monkey Pro-Strategizer 🐵
            </p>
            <p style="margin: 0;">
              <a href="#" style="color: #22c55e; text-decoration: none;">Manage Alert Settings</a>
            </p>
          </div>
        </div>
      </body>
      </html>
    `;

    // Send email using Resend API directly
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Finance Monkey <onboarding@resend.dev>",
        to: [to],
        subject: `🐵 Trade Alert: ${ruleName} - ${symbol} ${actionLabel}`,
        html: emailHtml,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Resend API error:", errorText);
      throw new Error(`Failed to send email: ${errorText}`);
    }

    const emailResponse = await response.json();
    console.log("Email sent successfully:", emailResponse);

    return new Response(JSON.stringify({ success: true, id: emailResponse.id }), {
      status: 200,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  } catch (error: unknown) {
    console.error("Error in send-trade-alert function:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      }
    );
  }
};

serve(handler);
