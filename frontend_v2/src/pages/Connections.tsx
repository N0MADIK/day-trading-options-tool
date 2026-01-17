import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Building2,
  TrendingUp,
  Wallet,
  CreditCard,
  Plus,
  Link2,
  CheckCircle2,
  Clock,
  XCircle,
  Search,
  ExternalLink,
  Shield,
  Zap,
  Eye,
  RefreshCw,
  PiggyBank,
  Loader2,
  FileSpreadsheet,
  Settings,
  Trash2,
  Database,
} from "lucide-react";
import { usePlaidLink } from "react-plaid-link";
import { useConnections } from "@/hooks/useConnections";
import { useAuth } from "@/hooks/useAuth";
import { usePlaid } from "@/hooks/usePlaid";
import { useSnapTrade } from "@/hooks/useSnapTrade";
import { CSVImport } from "@/components/connections/CSVImport";
import { MarketDataConnections } from "@/components/connections/MarketDataConnections";
import { api } from "@/lib/api";
import { toast } from "sonner";

interface Institution {
  id: string;
  name: string;
  type: "brokerage" | "bank" | "crypto" | "credit" | "retirement";
  logo: string;
  provider: "plaid" | "snaptrade" | "direct";
  testMode?: boolean;
}

const institutions: Institution[] = [
  // Brokerages (SnapTrade)
  { id: "robinhood", name: "Robinhood", type: "brokerage", logo: "🏹", provider: "snaptrade" },
  { id: "vanguard", name: "Vanguard", type: "brokerage", logo: "⛵", provider: "snaptrade" },
  { id: "fidelity", name: "Fidelity", type: "brokerage", logo: "💼", provider: "snaptrade" },
  { id: "td-ameritrade", name: "TD Ameritrade", type: "brokerage", logo: "📊", provider: "snaptrade" },
  { id: "schwab", name: "Charles Schwab", type: "brokerage", logo: "📈", provider: "snaptrade" },
  { id: "etrade", name: "E*TRADE", type: "brokerage", logo: "⭐", provider: "snaptrade" },
  { id: "interactive-brokers", name: "Interactive Brokers", type: "brokerage", logo: "🌐", provider: "snaptrade" },
  // Banks (Plaid)
  { id: "wells-fargo", name: "Wells Fargo", type: "bank", logo: "🐴", provider: "plaid" },
  { id: "chase", name: "Chase", type: "bank", logo: "🏦", provider: "plaid" },
  { id: "bank-of-america", name: "Bank of America", type: "bank", logo: "🏛️", provider: "plaid" },
  { id: "citi", name: "Citibank", type: "bank", logo: "🔵", provider: "plaid" },
  { id: "usbank", name: "US Bank", type: "bank", logo: "🇺🇸", provider: "plaid" },
  // Credit Cards (Plaid)
  { id: "chase-credit", name: "Chase Credit Cards", type: "credit", logo: "💳", provider: "plaid" },
  { id: "amex", name: "American Express", type: "credit", logo: "💎", provider: "plaid" },
  { id: "capital-one", name: "Capital One", type: "credit", logo: "💰", provider: "plaid" },
  { id: "discover", name: "Discover", type: "credit", logo: "🔶", provider: "plaid" },
  // Crypto (Direct API)
  { id: "coinbase", name: "Coinbase", type: "crypto", logo: "₿", provider: "direct" },
  { id: "binance", name: "Binance", type: "crypto", logo: "🔶", provider: "direct" },
  { id: "kraken", name: "Kraken", type: "crypto", logo: "🐙", provider: "direct" },
  // Retirement (SnapTrade)
  { id: "fidelity-401k", name: "Fidelity 401(k)", type: "retirement", logo: "🏦", provider: "snaptrade" },
  { id: "vanguard-ira", name: "Vanguard IRA", type: "retirement", logo: "⛵", provider: "snaptrade" },
  { id: "schwab-roth", name: "Schwab Roth IRA", type: "retirement", logo: "📈", provider: "snaptrade" },
];

const typeIcons = {
  brokerage: TrendingUp,
  bank: Building2,
  crypto: Wallet,
  credit: CreditCard,
  retirement: PiggyBank,
};

const typeLabels = {
  brokerage: "Brokerage",
  bank: "Bank",
  crypto: "Crypto Exchange",
  credit: "Credit Card",
  retirement: "Retirement",
};

const providerLabels = {
  plaid: { name: "Plaid", color: "bg-blue-500/10 text-blue-400 border-blue-500/30" },
  snaptrade: { name: "SnapTrade", color: "bg-purple-500/10 text-purple-400 border-purple-500/30" },
  direct: { name: "Direct API", color: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
};

export default function Connections() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { accounts, loading, disconnectAccount, syncAccount, fetchAccounts } = useConnections();
  const {
    createLinkToken,
    exchangeToken,
    getAccounts: getPlaidAccounts,
    getHoldings,
    isLoading: plaidLoading,
    linkToken,
    pendingInstitution,
    setPendingConnection
  } = usePlaid();
  const { registerUser, getLoginLink, getAccounts: getSnapTradeAccounts, userSecret, setUserSecret, isLoading: snapTradeLoading, ensureIntegration, syncIntegration } = useSnapTrade();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState("connected");
  const [connecting, setConnecting] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState<string | null>(null);

  // Handle SnapTrade redirect in popup
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get('status');
    const isPopup = window.opener && window.opener !== window;

    if (status && isPopup) {
      window.close();
    }
  }, []);

  // Load SnapTrade user secret from profile if exists
  useEffect(() => {
    const loadSnapTradeSecret = async () => {
      if (!user) return;
      try {
        const profile = await api.get<{ metadata?: { snaptrade_user_secret?: string } }>('/profiles/me').catch(() => null);

        // Check if metadata contains snaptrade secret
        if (profile?.metadata?.snaptrade_user_secret) {
          setUserSecret(profile.metadata.snaptrade_user_secret);
        }
      } catch (error) {
        console.error('Error loading SnapTrade secret:', error);
      }
    };
    loadSnapTradeSecret();
  }, [user, setUserSecret]);

  // Get connected institution IDs
  const connectedInstitutionIds = accounts.map(a => {
    const metadata = a.metadata as { institution_id?: string } | null;
    return metadata?.institution_id;
  }).filter(Boolean);

  const availableInstitutions = institutions.filter(i => !connectedInstitutionIds.includes(i.id));

  const filteredAvailable = availableInstitutions.filter((institution) => {
    const matchesSearch = institution.name.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === "all" || institution.type === filter;
    return matchesSearch && matchesFilter;
  });

  // Plaid Link success handler
  const handlePlaidSuccess = useCallback(async (publicToken: string, metadata: any) => {
    if (!user || !pendingInstitution) return;

    try {
      // Step 1: Exchange public token for access token via backend
      const exchangeResult = await api.post<{ access_token: string; item_id: string }>(
        '/integrations/plaid/exchange-token',
        { public_token: publicToken }
      );

      // Step 2: Create integration in backend (stores encrypted credentials)
      const integration = await api.post<{ id: number; integration_type: string; status: string }>(
        '/integrations',
        {
          integration_type: 'plaid',
          credentials: {
            access_token: exchangeResult.access_token
          },
          is_sandbox: false
        }
      );

      // Step 3: Trigger sync to create connected accounts
      await api.post(`/integrations/${integration.id}/sync`);

      toast.success(`Connected to ${pendingInstitution.name}!`);
      fetchAccounts();
      setActiveTab('connected');
    } catch (error: any) {
      console.error('Plaid connection error:', error);
      toast.error(`Failed to connect: ${error.message}`);
    } finally {
      setConnecting(null);
      setDialogOpen(null);
      setPendingConnection(null);
    }
  }, [user, pendingInstitution, fetchAccounts, setPendingConnection]);

  // Plaid Link hook
  const { open: openPlaidLink, ready: plaidLinkReady } = usePlaidLink({
    token: linkToken,
    onSuccess: handlePlaidSuccess,
    onExit: () => {
      setConnecting(null);
      setPendingConnection(null);
    },
  });

  // Connect via Plaid
  const connectPlaid = useCallback(async (institution: { id: string; name: string; type: string }) => {
    if (!user) return;

    setConnecting(institution.id);
    setPendingConnection(institution);

    try {
      // Create link token
      const token = await createLinkToken();
      if (!token) throw new Error('Failed to create Plaid link token');

      // Link will be opened via useEffect when token is ready
      toast.info('Opening Plaid Link...', { description: 'Complete the connection in the popup.' });
    } catch (error: any) {
      console.error('Plaid connection error:', error);
      toast.error(`Failed to connect: ${error.message}`);
      setConnecting(null);
      setPendingConnection(null);
    }
  }, [user, createLinkToken, setPendingConnection]);

  // Open Plaid Link when token is ready
  useEffect(() => {
    if (linkToken && pendingInstitution && plaidLinkReady) {
      openPlaidLink();
    }
  }, [linkToken, pendingInstitution, plaidLinkReady, openPlaidLink]);

  // Connect via SnapTrade
  // Connect via SnapTrade
  const connectSnapTrade = useCallback(async (institution: Institution) => {
    if (!user) return;

    setConnecting(institution.id);
    try {
      // Step 1: Register user with SnapTrade if not already registered
      let secret = userSecret;
      if (!secret) {
        secret = await registerUser();
        if (!secret) throw new Error('Failed to register with SnapTrade');
      }

      // Step 2: Get login link for the specific broker
      const loginUrl = await getLoginLink(secret, institution.id);

      if (!loginUrl) {
        throw new Error('Failed to get SnapTrade connection link');
      }

      // Open SnapTrade connection portal in a new window
      const popup = window.open(loginUrl, 'snaptrade-connect', 'width=600,height=800');

      toast.info('Complete the connection in the popup window', {
        description: 'Sign in to your brokerage account. Your credentials are handled securely by SnapTrade.',
        duration: 10000,
      });

      // Poll for popup closure
      const checkPopup = setInterval(async () => {
        if (popup?.closed) {
          clearInterval(checkPopup);

          toast.info('Syncing your accounts...');

          try {
            // Ensure integration record exists
            const integrationId = await ensureIntegration(secret || undefined);
            if (!integrationId) throw new Error('Failed to create integration record');

            // Trigger deep sync
            await syncIntegration(integrationId);

            toast.success('Accounts synced successfully!');
            fetchAccounts();
            setActiveTab('connected');
          } catch (error: any) {
            console.error('Sync error:', error);
            toast.error('Connection successful but sync failed. Please try syncing again.');
          } finally {
            setDialogOpen(null);
            setConnecting(null);
          }
        }
      }, 1000);

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(checkPopup);
        if (connecting === institution.id) {
          setConnecting(null);
        }
      }, 300000);

    } catch (error: any) {
      console.error('SnapTrade connection error:', error);
      toast.error(`Failed to connect: ${error.message}`);
      setConnecting(null);
    }
  }, [user, userSecret, registerUser, getLoginLink, getSnapTradeAccounts, accounts, fetchAccounts, connecting, ensureIntegration, syncIntegration]);

  const handleConnect = async (institutionId: string) => {
    const institution = institutions.find(i => i.id === institutionId);
    if (!institution) return;

    if (institution.provider === 'plaid') {
      await connectPlaid(institution);
    } else if (institution.provider === 'snaptrade') {
      await connectSnapTrade(institution);
    } else {
      // Direct API - show coming soon
      toast.info('Direct API integration coming soon!');
      setDialogOpen(null);
    }
  };

  const handleDisconnect = async (accountId: string) => {
    await disconnectAccount(accountId);
  };

  const handleSync = async (accountId: string) => {
    await syncAccount(accountId);
  };

  const getInstitutionForAccount = (account: typeof accounts[0]) => {
    const metadata = account.metadata as { institution_id?: string; provider?: string } | null;
    return institutions.find(i => i.id === metadata?.institution_id);
  };

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Shield className="h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold mb-2">Sign in Required</h2>
        <p className="text-muted-foreground mb-4">Please sign in to manage your financial connections</p>
        <Button onClick={() => navigate('/auth')}>Sign In</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Connections</h1>
          <p className="text-muted-foreground">
            Connect your real financial accounts using Plaid and SnapTrade
          </p>
        </div>
        <CSVImport onImportComplete={fetchAccounts} />
      </div>

      {/* Integration Providers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-blue-500/30 bg-blue-500/5">
          <CardContent className="flex items-center gap-4 p-4">
            <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Shield className="h-6 w-6 text-blue-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-blue-400">Plaid</h3>
              <p className="text-sm text-muted-foreground">
                Bank accounts, credit cards, and transaction data
              </p>
            </div>
            <Badge variant="outline" className="border-blue-500/30 text-blue-400">
              {plaidLoading ? 'Connecting...' : 'Ready'}
            </Badge>
          </CardContent>
        </Card>

        <Card className="border-purple-500/30 bg-purple-500/5">
          <CardContent className="flex items-center gap-4 p-4">
            <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Zap className="h-6 w-6 text-purple-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-purple-400">SnapTrade</h3>
              <p className="text-sm text-muted-foreground">
                Brokerage accounts, portfolios, and trading data
              </p>
            </div>
            <Badge variant="outline" className="border-purple-500/30 text-purple-400">
              {snapTradeLoading ? 'Connecting...' : userSecret ? 'Registered' : 'Ready'}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Connection Info */}
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="flex items-center gap-4 p-4">
          <Shield className="h-8 w-8 text-primary" />
          <div>
            <p className="font-medium">Secure Connection</p>
            <p className="text-sm text-muted-foreground">
              Your credentials are securely handled by Plaid and SnapTrade. WealthOS never sees your login details.
              Connect your real accounts from Wells Fargo, Vanguard, Robinhood, Chase, Fidelity, and more.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Market Data Connections Section */}
      <MarketDataConnections />

      {/* CSV Data Sources Section */}
      {accounts.filter(a => (a.metadata as any)?.source === "csv_import").length > 0 && (
        <Card className="border-orange-500/30 bg-orange-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                  <FileSpreadsheet className="h-5 w-5 text-orange-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-orange-400">CSV Data Sources</CardTitle>
                  <CardDescription>Manually imported data from CSV files</CardDescription>
                </div>
              </div>
              <Badge variant="outline" className="border-orange-500/30 text-orange-400">
                {accounts.filter(a => (a.metadata as any)?.source === "csv_import").length} source(s)
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {accounts
                .filter(a => (a.metadata as any)?.source === "csv_import")
                .map((source) => {
                  const metadata = source.metadata as { file_name?: string; imported_at?: string } | null;
                  return (
                    <div key={source.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 border border-border">
                      <div className="flex items-center gap-3">
                        <FileSpreadsheet className="h-5 w-5 text-orange-400" />
                        <div>
                          <p className="font-medium">{source.account_name}</p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>Imported {metadata?.imported_at ? new Date(metadata.imported_at).toLocaleDateString() : 'recently'}</span>
                            {metadata?.file_name && <span>• {metadata.file_name}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          ${(source.balance || 0).toLocaleString()}
                        </Badge>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <Settings className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-2">
                                <FileSpreadsheet className="h-5 w-5 text-orange-400" />
                                {source.account_name}
                              </DialogTitle>
                              <DialogDescription>
                                Manage this CSV data source
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                              <div className="p-4 bg-secondary rounded-lg space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-muted-foreground">Source Type</span>
                                  <span className="font-medium">CSV Import</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-muted-foreground">Account Type</span>
                                  <span className="font-medium capitalize">{source.institution_type}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-muted-foreground">Balance</span>
                                  <span className="font-medium">${(source.balance || 0).toLocaleString()}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-muted-foreground">Imported</span>
                                  <span className="font-medium">
                                    {metadata?.imported_at ? new Date(metadata.imported_at).toLocaleString() : 'Unknown'}
                                  </span>
                                </div>
                              </div>

                              <div className="p-4 bg-secondary rounded-lg">
                                <h4 className="font-medium mb-2 flex items-center gap-2">
                                  <Database className="h-4 w-4" />
                                  Data Saved To
                                </h4>
                                <ul className="space-y-1 text-sm text-muted-foreground">
                                  <li className="flex items-center gap-2">
                                    <CheckCircle2 className="h-3 w-3 text-primary" />
                                    Holdings (Dashboard, Financial Breakdown)
                                  </li>
                                  <li className="flex items-center gap-2">
                                    <CheckCircle2 className="h-3 w-3 text-primary" />
                                    Transactions (Trade History, Recent Activity)
                                  </li>
                                  <li className="flex items-center gap-2">
                                    <CheckCircle2 className="h-3 w-3 text-primary" />
                                    Account Balance (Net Worth calculation)
                                  </li>
                                </ul>
                              </div>
                            </div>
                            <DialogFooter>
                              <Button
                                variant="destructive"
                                onClick={async () => {
                                  await handleDisconnect(source.id);
                                }}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete Source & Data
                              </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                        <Link to={`/account/${source.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  );
                })}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="connected">
            Connected ({accounts.filter(a => (a.metadata as any)?.source !== "csv_import").length})
          </TabsTrigger>
          <TabsTrigger value="available">Add New Connection</TabsTrigger>
        </TabsList>

        <TabsContent value="connected" className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : accounts.filter(a => (a.metadata as any)?.source !== "csv_import").length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Link2 className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">No connected accounts</p>
                <p className="text-sm text-muted-foreground mb-4">Connect your first account to get started, or import via CSV</p>
                <div className="flex gap-2">
                  <Button onClick={() => setActiveTab("available")}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Connection
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {accounts
                .filter(a => (a.metadata as any)?.source !== "csv_import")
                .map((account) => {
                  const institution = getInstitutionForAccount(account);
                  const Icon = institution ? typeIcons[institution.type] : Building2;
                  const metadata = account.metadata as { provider?: string } | null;
                  const providerStyle = providerLabels[metadata?.provider as keyof typeof providerLabels] || providerLabels.plaid;

                  return (
                    <Card key={account.id} className="border-primary/20 hover:border-primary/40 transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center text-2xl">
                              {institution?.logo || "🏦"}
                            </div>
                            <div>
                              <h3 className="font-semibold">{account.institution_name}</h3>
                              <div className="flex items-center gap-2">
                                <Icon className="h-3 w-3 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground">
                                  {account.institution_type}
                                </span>
                              </div>
                            </div>
                          </div>
                          <Badge variant="outline" className={providerStyle.color}>
                            {providerStyle.name}
                          </Badge>
                        </div>

                        <div className="mb-3 p-3 rounded-lg bg-secondary/50">
                          <p className="text-sm text-muted-foreground">Balance</p>
                          <p className="text-xl font-bold">
                            ${(account.balance || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </p>
                          {account.account_number_masked && (
                            <p className="text-xs text-muted-foreground">
                              Account {account.account_number_masked}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            <span>
                              Synced {account.last_synced_at
                                ? new Date(account.last_synced_at).toLocaleDateString()
                                : 'Never'}
                            </span>
                          </div>
                          <Badge variant="outline" className={account.is_connected ? "border-primary text-primary" : "border-destructive text-destructive"}>
                            {account.is_connected ? (
                              <><CheckCircle2 className="h-3 w-3 mr-1" />Active</>
                            ) : (
                              <><XCircle className="h-3 w-3 mr-1" />Disconnected</>
                            )}
                          </Badge>
                        </div>

                        <div className="flex gap-2">
                          <Link to={`/account/${account.id}`} className="flex-1">
                            <Button variant="outline" size="sm" className="w-full">
                              <Eye className="h-4 w-4 mr-2" />
                              View
                            </Button>
                          </Link>
                          <Button variant="outline" size="sm" onClick={() => handleSync(account.id)}>
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDisconnect(account.id)}
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="available" className="mt-6 space-y-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search institutions..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {["all", "brokerage", "bank", "credit", "crypto", "retirement"].map((type) => (
                <Button
                  key={type}
                  variant={filter === type ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilter(type)}
                >
                  {type === "all" ? "All" : typeLabels[type as keyof typeof typeLabels]}
                </Button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAvailable.map((institution) => {
              const Icon = typeIcons[institution.type];
              const providerStyle = providerLabels[institution.provider];
              return (
                <Card key={institution.id} className="hover:border-primary/30 transition-colors group">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center text-2xl">
                          {institution.logo}
                        </div>
                        <div>
                          <h3 className="font-semibold">{institution.name}</h3>
                          <div className="flex items-center gap-2">
                            <Icon className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              {typeLabels[institution.type]}
                            </span>
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline" className={providerStyle.color}>
                        {providerStyle.name}
                      </Badge>
                    </div>
                    <Dialog open={dialogOpen === institution.id} onOpenChange={(open) => setDialogOpen(open ? institution.id : null)}>
                      <DialogTrigger asChild>
                        <Button className="w-full">
                          <Link2 className="h-4 w-4 mr-2" />
                          Connect via {providerStyle.name}
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-3">
                            <span className="text-3xl">{institution.logo}</span>
                            Connect to {institution.name}
                          </DialogTitle>
                          <DialogDescription>
                            You'll be redirected to {providerStyle.name} to securely authorize WealthOS to access your account data.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 pt-4">
                          <div className="p-4 bg-secondary rounded-lg">
                            <h4 className="font-medium mb-2">WealthOS will have access to:</h4>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                              <li className="flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4 text-primary" />
                                Account balances and holdings
                              </li>
                              <li className="flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4 text-primary" />
                                Transaction history
                              </li>
                              {(institution.type === "brokerage" || institution.type === "retirement") && (
                                <li className="flex items-center gap-2">
                                  <CheckCircle2 className="h-4 w-4 text-primary" />
                                  Portfolio positions and performance
                                </li>
                              )}
                              <li className="flex items-center gap-2">
                                <XCircle className="h-4 w-4 text-destructive" />
                                No ability to make trades or transfers
                              </li>
                            </ul>
                          </div>
                          <Button
                            className="w-full"
                            onClick={() => handleConnect(institution.id)}
                            disabled={connecting === institution.id}
                          >
                            {connecting === institution.id ? (
                              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Connecting...</>
                            ) : (
                              <><ExternalLink className="h-4 w-4 mr-2" />Continue with {providerStyle.name}</>
                            )}
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {filteredAvailable.length === 0 && (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Search className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">No institutions found</p>
                <p className="text-sm text-muted-foreground">
                  Try adjusting your search or filter
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
