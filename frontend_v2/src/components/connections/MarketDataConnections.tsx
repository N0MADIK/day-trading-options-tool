import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  LineChart,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Loader2,
  Settings,
  Trash2,
  Lock,
  Key,
  Plus,
} from 'lucide-react';
import {
  useMarketDataConnections,
  MARKET_DATA_PROVIDERS,
  type MarketDataProvider,
} from '@/hooks/useMarketDataConnections';
import { useAuth } from '@/hooks/useAuth';

export function MarketDataConnections() {
  const { user } = useAuth();
  const {
    subscriptions,
    loading,
    connectProvider,
    disconnectProvider,
    updateCredentials,
    getProviderStatus,
  } = useMarketDataConnections();

  const [connectingId, setConnectingId] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<Record<string, string>>({});

  const handleConnect = async (provider: MarketDataProvider) => {
    setConnectingId(provider.id);
    
    if (provider.requiresAuth && provider.authFields) {
      // Validate all fields are filled
      const missingFields = provider.authFields.filter((f) => !credentials[f.name]?.trim());
      if (missingFields.length > 0) {
        setConnectingId(null);
        return;
      }
    }

    const success = await connectProvider(provider.id, provider.requiresAuth ? credentials : undefined);
    
    if (success) {
      setDialogOpen(null);
      setCredentials({});
    }
    setConnectingId(null);
  };

  const handleDisconnect = async (subscriptionId: string) => {
    await disconnectProvider(subscriptionId);
    setSettingsOpen(null);
  };

  const handleUpdateCredentials = async (subscriptionId: string) => {
    const success = await updateCredentials(subscriptionId, credentials);
    if (success) {
      setSettingsOpen(null);
      setCredentials({});
    }
  };

  const connectedProviders = subscriptions.map((s) => s.provider_name);

  if (!user) return null;

  return (
    <Card className="border-cyan-500/30 bg-cyan-500/5">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center">
              <LineChart className="h-5 w-5 text-cyan-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-cyan-400">Market Data Connections</CardTitle>
              <CardDescription>
                Connect to market data providers for real-time quotes and trading
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="border-cyan-500/30 text-cyan-400">
            {subscriptions.length} connected
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connected Providers */}
        {subscriptions.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Active Connections</p>
            <div className="space-y-2">
              {subscriptions.map((sub) => {
                const provider = MARKET_DATA_PROVIDERS.find((p) => p.id === sub.provider_name);
                if (!provider) return null;

                return (
                  <div
                    key={sub.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 border border-border"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{provider.logo}</span>
                      <div>
                        <p className="font-medium">{provider.name}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          {sub.has_credentials ? (
                            <>
                              <Lock className="h-3 w-3 text-primary" />
                              <span>Credentials saved</span>
                            </>
                          ) : (
                            <span>Free tier</span>
                          )}
                          <span>•</span>
                          <span>Connected {new Date(sub.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={
                          sub.is_active
                            ? 'border-primary text-primary'
                            : 'border-destructive text-destructive'
                        }
                      >
                        {sub.is_active ? (
                          <>
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Active
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3 w-3 mr-1" />
                            Inactive
                          </>
                        )}
                      </Badge>
                      <Dialog
                        open={settingsOpen === sub.id}
                        onOpenChange={(open) => {
                          setSettingsOpen(open ? sub.id : null);
                          if (!open) setCredentials({});
                        }}
                      >
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <Settings className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle className="flex items-center gap-2">
                              <span className="text-2xl">{provider.logo}</span>
                              {provider.name} Settings
                            </DialogTitle>
                            <DialogDescription>
                              Manage your connection to {provider.name}
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4 py-4">
                            <div className="p-4 bg-secondary rounded-lg space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Provider Type</span>
                                <span className="font-medium capitalize">{sub.provider_type}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Status</span>
                                <Badge variant="outline" className="border-primary text-primary">
                                  Active
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Connected</span>
                                <span className="font-medium">
                                  {new Date(sub.created_at).toLocaleDateString()}
                                </span>
                              </div>
                            </div>

                            {provider.requiresAuth && provider.authFields && (
                              <div className="space-y-3">
                                <p className="text-sm font-medium">Update Credentials</p>
                                {provider.authFields.map((field) => (
                                  <div key={field.name} className="space-y-2">
                                    <Label htmlFor={`update-${field.name}`}>{field.label}</Label>
                                    <Input
                                      id={`update-${field.name}`}
                                      type={field.type}
                                      placeholder={field.placeholder}
                                      value={credentials[field.name] || ''}
                                      onChange={(e) =>
                                        setCredentials((prev) => ({
                                          ...prev,
                                          [field.name]: e.target.value,
                                        }))
                                      }
                                    />
                                  </div>
                                ))}
                                <Button
                                  variant="outline"
                                  className="w-full"
                                  onClick={() => handleUpdateCredentials(sub.id)}
                                  disabled={
                                    !provider.authFields.every((f) => credentials[f.name]?.trim())
                                  }
                                >
                                  <Key className="h-4 w-4 mr-2" />
                                  Update Credentials
                                </Button>
                              </div>
                            )}

                            {provider.docsUrl && (
                              <a
                                href={provider.docsUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-sm text-primary hover:underline"
                              >
                                <ExternalLink className="h-4 w-4" />
                                View API Documentation
                              </a>
                            )}
                          </div>
                          <DialogFooter>
                            <Button
                              variant="destructive"
                              onClick={() => handleDisconnect(sub.id)}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Disconnect
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Available Providers */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            {subscriptions.length > 0 ? 'Add More Providers' : 'Available Providers'}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {MARKET_DATA_PROVIDERS.filter((p) => !connectedProviders.includes(p.id)).map(
              (provider) => (
                <Dialog
                  key={provider.id}
                  open={dialogOpen === provider.id}
                  onOpenChange={(open) => {
                    setDialogOpen(open ? provider.id : null);
                    if (!open) setCredentials({});
                  }}
                >
                  <DialogTrigger asChild>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30 border border-border hover:border-primary/30 cursor-pointer transition-colors">
                      <span className="text-2xl">{provider.logo}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{provider.name}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {provider.requiresAuth ? 'API Key Required' : 'Free - No API Key'}
                        </p>
                      </div>
                      <Plus className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle className="flex items-center gap-3">
                        <span className="text-3xl">{provider.logo}</span>
                        Connect to {provider.name}
                      </DialogTitle>
                      <DialogDescription>{provider.description}</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      {/* Features */}
                      <div className="p-4 bg-secondary rounded-lg">
                        <h4 className="font-medium mb-2">Features</h4>
                        <ul className="space-y-1 text-sm text-muted-foreground">
                          {provider.features.map((feature) => (
                            <li key={feature} className="flex items-center gap-2">
                              <CheckCircle2 className="h-4 w-4 text-primary" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Auth Fields */}
                      {provider.requiresAuth && provider.authFields && (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Lock className="h-4 w-4" />
                            <span>Your credentials are encrypted before storage</span>
                          </div>
                          {provider.authFields.map((field) => (
                            <div key={field.name} className="space-y-2">
                              <Label htmlFor={field.name}>{field.label}</Label>
                              <Input
                                id={field.name}
                                type={field.type}
                                placeholder={field.placeholder}
                                value={credentials[field.name] || ''}
                                onChange={(e) =>
                                  setCredentials((prev) => ({
                                    ...prev,
                                    [field.name]: e.target.value,
                                  }))
                                }
                              />
                            </div>
                          ))}
                        </div>
                      )}

                      {provider.docsUrl && (
                        <a
                          href={provider.docsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-sm text-primary hover:underline"
                        >
                          <ExternalLink className="h-4 w-4" />
                          Get API credentials from {provider.name}
                        </a>
                      )}
                    </div>
                    <DialogFooter>
                      <Button
                        onClick={() => handleConnect(provider)}
                        disabled={
                          connectingId === provider.id ||
                          (provider.requiresAuth &&
                            provider.authFields &&
                            !provider.authFields.every((f) => credentials[f.name]?.trim()))
                        }
                      >
                        {connectingId === provider.id ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Connecting...
                          </>
                        ) : (
                          <>
                            <Plus className="h-4 w-4 mr-2" />
                            Connect
                          </>
                        )}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              )
            )}
          </div>
        </div>

        {/* Default provider info */}
        {!connectedProviders.includes('yfinance') && subscriptions.length === 0 && (
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <p className="text-sm text-primary">
              <strong>Tip:</strong> Yahoo Finance is free and provides comprehensive market data.
              It's recommended as your default data source.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
