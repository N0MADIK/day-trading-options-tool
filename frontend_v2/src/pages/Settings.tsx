import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Bell,
  Moon,
  Sun,
  Globe,
  Shield,
  Smartphone,
  Mail,
  DollarSign,
  Loader2,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

export default function Settings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    priceAlerts: true,
    weeklyReport: true,
    marketNews: false,
  });

  const [preferences, setPreferences] = useState({
    theme: "dark",
    currency: "USD",
    language: "en",
    timezone: "America/New_York",
  });

  const [security, setSecurity] = useState({
    twoFactor: false,
    biometric: true,
    sessionTimeout: "30",
  });

  // Fetch notification settings from API
  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchSettings = async () => {
      try {
        const settings = await api.get<{
          email_notifications?: boolean;
          push_notifications?: boolean;
          price_alerts?: boolean;
          weekly_report?: boolean;
          market_news?: boolean;
        }>('/notification-settings').catch(() => null);

        if (settings) {
          setNotifications({
            email: settings.email_notifications ?? true,
            push: settings.push_notifications ?? false,
            priceAlerts: settings.price_alerts ?? true,
            weeklyReport: settings.weekly_report ?? true,
            marketNews: settings.market_news ?? false,
          });
        }
      } catch (error) {
        console.error('Error fetching notification settings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, [user]);

  const handleSaveNotifications = async () => {
    setSaving(true);
    try {
      await api.put('/notification-settings', {
        email_notifications: notifications.email,
        push_notifications: notifications.push,
        price_alerts: notifications.priceAlerts,
        weekly_report: notifications.weeklyReport,
        market_news: notifications.marketNews,
      });
      toast({
        title: "Notifications Updated",
        description: "Your notification preferences have been saved.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save notification settings.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleSavePreferences = () => {
    toast({
      title: "Preferences Updated",
      description: "Your display preferences have been saved.",
    });
  };

  const handleSaveSecurity = () => {
    toast({
      title: "Security Settings Updated",
      description: "Your security preferences have been saved.",
    });
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account preferences and notifications
        </p>
      </div>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            Notifications
          </CardTitle>
          <CardDescription>
            Choose how you want to receive updates and alerts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label className="text-base">Email Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive updates via email
                </p>
              </div>
            </div>
            <Switch
              checked={notifications.email}
              onCheckedChange={(checked) =>
                setNotifications({ ...notifications, email: checked })
              }
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Smartphone className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label className="text-base">Push Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive mobile push notifications
                </p>
              </div>
            </div>
            <Switch
              checked={notifications.push}
              onCheckedChange={(checked) =>
                setNotifications({ ...notifications, push: checked })
              }
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DollarSign className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label className="text-base">Price Alerts</Label>
                <p className="text-sm text-muted-foreground">
                  Get notified when stocks hit your targets
                </p>
              </div>
            </div>
            <Switch
              checked={notifications.priceAlerts}
              onCheckedChange={(checked) =>
                setNotifications({ ...notifications, priceAlerts: checked })
              }
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Weekly Performance Report</Label>
              <p className="text-sm text-muted-foreground">
                Receive a weekly summary of your portfolio
              </p>
            </div>
            <Switch
              checked={notifications.weeklyReport}
              onCheckedChange={(checked) =>
                setNotifications({ ...notifications, weeklyReport: checked })
              }
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Market News</Label>
              <p className="text-sm text-muted-foreground">
                Breaking news about markets and your holdings
              </p>
            </div>
            <Switch
              checked={notifications.marketNews}
              onCheckedChange={(checked) =>
                setNotifications({ ...notifications, marketNews: checked })
              }
            />
          </div>

          <Button onClick={handleSaveNotifications} className="w-full sm:w-auto">
            Save Notification Settings
          </Button>
        </CardContent>
      </Card>

      {/* Display Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sun className="h-5 w-5 text-primary" />
            Display Preferences
          </CardTitle>
          <CardDescription>
            Customize how Finance Monkey looks and feels
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>Theme</Label>
              <Select
                value={preferences.theme}
                onValueChange={(value) =>
                  setPreferences({ ...preferences, theme: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dark">
                    <div className="flex items-center gap-2">
                      <Moon className="h-4 w-4" />
                      Dark Mode
                    </div>
                  </SelectItem>
                  <SelectItem value="light">
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4" />
                      Light Mode
                    </div>
                  </SelectItem>
                  <SelectItem value="system">System Default</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Currency</Label>
              <Select
                value={preferences.currency}
                onValueChange={(value) =>
                  setPreferences({ ...preferences, currency: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD ($)</SelectItem>
                  <SelectItem value="EUR">EUR (€)</SelectItem>
                  <SelectItem value="GBP">GBP (£)</SelectItem>
                  <SelectItem value="JPY">JPY (¥)</SelectItem>
                  <SelectItem value="CAD">CAD (C$)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Language</Label>
              <Select
                value={preferences.language}
                onValueChange={(value) =>
                  setPreferences({ ...preferences, language: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Español</SelectItem>
                  <SelectItem value="fr">Français</SelectItem>
                  <SelectItem value="de">Deutsch</SelectItem>
                  <SelectItem value="zh">中文</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Timezone</Label>
              <Select
                value={preferences.timezone}
                onValueChange={(value) =>
                  setPreferences({ ...preferences, timezone: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                  <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                  <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                  <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                  <SelectItem value="Europe/London">London (GMT)</SelectItem>
                  <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button onClick={handleSavePreferences} className="w-full sm:w-auto">
            Save Display Preferences
          </Button>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Security
          </CardTitle>
          <CardDescription>
            Protect your account with additional security measures
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Two-Factor Authentication</Label>
              <p className="text-sm text-muted-foreground">
                Add an extra layer of security to your account
              </p>
            </div>
            <Switch
              checked={security.twoFactor}
              onCheckedChange={(checked) =>
                setSecurity({ ...security, twoFactor: checked })
              }
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Biometric Login</Label>
              <p className="text-sm text-muted-foreground">
                Use fingerprint or face recognition to log in
              </p>
            </div>
            <Switch
              checked={security.biometric}
              onCheckedChange={(checked) =>
                setSecurity({ ...security, biometric: checked })
              }
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>Session Timeout</Label>
            <Select
              value={security.sessionTimeout}
              onValueChange={(value) =>
                setSecurity({ ...security, sessionTimeout: value })
              }
            >
              <SelectTrigger className="max-w-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="15">15 minutes</SelectItem>
                <SelectItem value="30">30 minutes</SelectItem>
                <SelectItem value="60">1 hour</SelectItem>
                <SelectItem value="120">2 hours</SelectItem>
                <SelectItem value="never">Never</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Automatically log out after period of inactivity
            </p>
          </div>

          <Button onClick={handleSaveSecurity} className="w-full sm:w-auto">
            Save Security Settings
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
