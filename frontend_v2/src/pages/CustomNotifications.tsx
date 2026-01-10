import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  Bell,
  Plus,
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  Building2,
  LineChart,
  AlertTriangle,
  Clock,
  Mail,
  Smartphone,
  MessageSquare,
  Trash2,
  Settings2,
  Activity,
  Loader2,
  Edit,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

interface NotificationRule {
  id: string;
  rule_name: string;
  rule_type: string;
  indicator_type: string | null;
  conditions: Record<string, any>;
  is_enabled: boolean;
  frequency: string;
  urgency_level: string;
  sensitivity: number;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  notify_email: boolean;
  notify_push: boolean;
  notify_sms: boolean;
  last_triggered_at: string | null;
  trigger_count: number;
}

const ruleCategories = [
  {
    id: "account",
    name: "Account Indicators",
    icon: Building2,
    description: "Net worth changes, account balance alerts",
    indicators: [
      { id: "balance_change", name: "Balance Change", description: "Alert when account balance changes by threshold" },
      { id: "net_worth_milestone", name: "Net Worth Milestone", description: "Notify at net worth milestones" },
      { id: "account_sync_issue", name: "Sync Issues", description: "Alert when account fails to sync" },
      { id: "low_balance", name: "Low Balance Warning", description: "Warn when balance falls below threshold" },
    ],
  },
  {
    id: "trade",
    name: "Trade Indicators",
    icon: TrendingUp,
    description: "Position changes, trade executions",
    indicators: [
      { id: "position_change", name: "Position Change", description: "Alert on position size changes" },
      { id: "trade_execution", name: "Trade Executed", description: "Notify when trades are executed" },
      { id: "dividend_received", name: "Dividend Received", description: "Alert on dividend payments" },
      { id: "cost_basis_change", name: "Cost Basis Change", description: "Track changes to cost basis" },
    ],
  },
  {
    id: "market",
    name: "Market Indicators",
    icon: LineChart,
    description: "Price alerts, market movements",
    indicators: [
      { id: "price_target", name: "Price Target Hit", description: "Alert when stock hits target price" },
      { id: "percent_change", name: "Percent Change", description: "Alert on significant price movements" },
      { id: "volume_spike", name: "Volume Spike", description: "Detect unusual trading volume" },
      { id: "52_week_high_low", name: "52-Week High/Low", description: "Alert on new highs or lows" },
    ],
  },
  {
    id: "bank_change",
    name: "Bank Account Changes",
    icon: DollarSign,
    description: "Large deposits, withdrawals",
    indicators: [
      { id: "large_deposit", name: "Large Deposit", description: "Alert on large incoming deposits" },
      { id: "large_withdrawal", name: "Large Withdrawal", description: "Alert on large outgoing withdrawals" },
      { id: "recurring_change", name: "Recurring Payment Change", description: "Detect changes in recurring payments" },
      { id: "unusual_activity", name: "Unusual Activity", description: "Flag unusual transaction patterns" },
    ],
  },
  {
    id: "credit_card",
    name: "Credit Card Alerts",
    icon: CreditCard,
    description: "Large charges, payment reminders",
    indicators: [
      { id: "large_charge", name: "Large Charge", description: "Alert on charges above threshold" },
      { id: "payment_due", name: "Payment Due Soon", description: "Reminder before payment due date" },
      { id: "credit_utilization", name: "Credit Utilization", description: "Alert on high utilization" },
      { id: "foreign_transaction", name: "Foreign Transaction", description: "Alert on international charges" },
    ],
  },
];

const frequencyOptions = [
  { value: "immediate", label: "Immediate" },
  { value: "hourly", label: "Hourly Digest" },
  { value: "daily", label: "Daily Summary" },
  { value: "weekly", label: "Weekly Digest" },
];

const urgencyOptions = [
  { value: "low", label: "Low", color: "bg-muted text-muted-foreground" },
  { value: "normal", label: "Normal", color: "bg-primary/20 text-primary" },
  { value: "high", label: "High", color: "bg-orange-500/20 text-orange-500" },
  { value: "critical", label: "Critical", color: "bg-destructive/20 text-destructive" },
];

export default function CustomNotifications() {
  const { user } = useAuth();
  const [rules, setRules] = useState<NotificationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    rule_name: "",
    rule_type: "",
    indicator_type: "",
    threshold: "100",
    comparison: "greater",
    frequency: "immediate",
    urgency_level: "normal",
    sensitivity: 5,
    quiet_hours_enabled: false,
    quiet_hours_start: "22:00",
    quiet_hours_end: "08:00",
    notify_email: true,
    notify_push: false,
    notify_sms: false,
  });

  useEffect(() => {
    if (user) {
      fetchRules();
    }
  }, [user]);

  const fetchRules = async () => {
    try {
      const data = await api.get<NotificationRule[]>('/custom-notification-rules');
      setRules(data || []);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      rule_name: "",
      rule_type: "",
      indicator_type: "",
      threshold: "100",
      comparison: "greater",
      frequency: "immediate",
      urgency_level: "normal",
      sensitivity: 5,
      quiet_hours_enabled: false,
      quiet_hours_start: "22:00",
      quiet_hours_end: "08:00",
      notify_email: true,
      notify_push: false,
      notify_sms: false,
    });
    setEditingRule(null);
  };

  const handleSaveRule = async () => {
    if (!user || !formData.rule_name || !formData.rule_type || !formData.indicator_type) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      const ruleData = {
        rule_name: formData.rule_name,
        rule_type: formData.rule_type,
        indicator_type: formData.indicator_type,
        conditions: {
          threshold: parseFloat(formData.threshold),
          comparison: formData.comparison,
        },
        frequency: formData.frequency,
        urgency_level: formData.urgency_level,
        sensitivity: formData.sensitivity,
        quiet_hours_start: formData.quiet_hours_enabled ? formData.quiet_hours_start : null,
        quiet_hours_end: formData.quiet_hours_enabled ? formData.quiet_hours_end : null,
        notify_email: formData.notify_email,
        notify_push: formData.notify_push,
        notify_sms: formData.notify_sms,
      };

      if (editingRule) {
        await api.put(`/custom-notification-rules/${editingRule.id}`, ruleData);
        toast({ title: "Rule Updated", description: "Your notification rule has been updated" });
      } else {
        await api.post('/custom-notification-rules', ruleData);
        toast({ title: "Rule Created", description: "Your notification rule has been created" });
      }

      fetchRules();
      setDialogOpen(false);
      resetForm();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleRule = async (rule: NotificationRule) => {
    try {
      await api.put(`/custom-notification-rules/${rule.id}`, { is_enabled: !rule.is_enabled });
      fetchRules();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await api.delete(`/custom-notification-rules/${ruleId}`);
      toast({ title: "Rule Deleted", description: "The notification rule has been removed" });
      fetchRules();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const handleEditRule = (rule: NotificationRule) => {
    setEditingRule(rule);
    setFormData({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      indicator_type: rule.indicator_type || "",
      threshold: rule.conditions?.threshold?.toString() || "100",
      comparison: rule.conditions?.comparison || "greater",
      frequency: rule.frequency,
      urgency_level: rule.urgency_level,
      sensitivity: rule.sensitivity || 5,
      quiet_hours_enabled: !!rule.quiet_hours_start,
      quiet_hours_start: rule.quiet_hours_start || "22:00",
      quiet_hours_end: rule.quiet_hours_end || "08:00",
      notify_email: rule.notify_email,
      notify_push: rule.notify_push,
      notify_sms: rule.notify_sms,
    });
    setDialogOpen(true);
  };

  const getIndicatorInfo = (ruleType: string, indicatorType: string | null) => {
    const category = ruleCategories.find(c => c.id === ruleType);
    if (!category || !indicatorType) return null;
    return category.indicators.find(i => i.id === indicatorType);
  };

  const getCategoryInfo = (ruleType: string) => {
    return ruleCategories.find(c => c.id === ruleType);
  };

  const selectedCategory = ruleCategories.find(c => c.id === formData.rule_type);

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Custom Notifications</h1>
          <p className="text-muted-foreground">
            Set up personalized alerts for your financial accounts and market activity
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Rule
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingRule ? "Edit" : "Create"} Notification Rule</DialogTitle>
              <DialogDescription>
                Configure when and how you want to be notified
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-4">
              {/* Rule Name */}
              <div className="space-y-2">
                <Label>Rule Name</Label>
                <Input
                  placeholder="e.g., Large Withdrawal Alert"
                  value={formData.rule_name}
                  onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                />
              </div>

              {/* Category Selection */}
              <div className="space-y-2">
                <Label>Alert Category</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {ruleCategories.map((category) => (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, rule_type: category.id, indicator_type: "" })}
                      className={`p-3 rounded-lg border text-left transition-colors ${formData.rule_type === category.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:bg-muted"
                        }`}
                    >
                      <category.icon className="h-5 w-5 mb-1" />
                      <p className="text-sm font-medium">{category.name}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Indicator Selection */}
              {selectedCategory && (
                <div className="space-y-2">
                  <Label>Indicator Type</Label>
                  <Select
                    value={formData.indicator_type}
                    onValueChange={(value) => setFormData({ ...formData, indicator_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select indicator" />
                    </SelectTrigger>
                    <SelectContent>
                      {selectedCategory.indicators.map((indicator) => (
                        <SelectItem key={indicator.id} value={indicator.id}>
                          <div>
                            <p>{indicator.name}</p>
                            <p className="text-xs text-muted-foreground">{indicator.description}</p>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Threshold Settings */}
              {formData.indicator_type && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Condition</Label>
                    <Select
                      value={formData.comparison}
                      onValueChange={(value) => setFormData({ ...formData, comparison: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="greater">Greater than</SelectItem>
                        <SelectItem value="less">Less than</SelectItem>
                        <SelectItem value="equals">Equals</SelectItem>
                        <SelectItem value="any">Any change</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Threshold ($)</Label>
                    <Input
                      type="number"
                      value={formData.threshold}
                      onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
                    />
                  </div>
                </div>
              )}

              <Separator />

              {/* Notification Timing */}
              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Notification Timing
                </h4>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Frequency</Label>
                    <Select
                      value={formData.frequency}
                      onValueChange={(value) => setFormData({ ...formData, frequency: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {frequencyOptions.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Urgency Level</Label>
                    <Select
                      value={formData.urgency_level}
                      onValueChange={(value) => setFormData({ ...formData, urgency_level: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {urgencyOptions.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Sensitivity (1-10)</Label>
                    <span className="text-sm text-muted-foreground">{formData.sensitivity}</span>
                  </div>
                  <Slider
                    value={[formData.sensitivity]}
                    onValueChange={(value) => setFormData({ ...formData, sensitivity: value[0] })}
                    min={1}
                    max={10}
                    step={1}
                  />
                  <p className="text-xs text-muted-foreground">
                    Higher sensitivity = more frequent notifications
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Quiet Hours</Label>
                      <p className="text-sm text-muted-foreground">Pause notifications during specific hours</p>
                    </div>
                    <Switch
                      checked={formData.quiet_hours_enabled}
                      onCheckedChange={(checked) => setFormData({ ...formData, quiet_hours_enabled: checked })}
                    />
                  </div>
                  {formData.quiet_hours_enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Start Time</Label>
                        <Input
                          type="time"
                          value={formData.quiet_hours_start}
                          onChange={(e) => setFormData({ ...formData, quiet_hours_start: e.target.value })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>End Time</Label>
                        <Input
                          type="time"
                          value={formData.quiet_hours_end}
                          onChange={(e) => setFormData({ ...formData, quiet_hours_end: e.target.value })}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Delivery Methods */}
              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Delivery Methods
                </h4>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <span>Email Notifications</span>
                    </div>
                    <Switch
                      checked={formData.notify_email}
                      onCheckedChange={(checked) => setFormData({ ...formData, notify_email: checked })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Smartphone className="h-4 w-4 text-muted-foreground" />
                      <span>Push Notifications</span>
                    </div>
                    <Switch
                      checked={formData.notify_push}
                      onCheckedChange={(checked) => setFormData({ ...formData, notify_push: checked })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <span>SMS Alerts</span>
                    </div>
                    <Switch
                      checked={formData.notify_sms}
                      onCheckedChange={(checked) => setFormData({ ...formData, notify_sms: checked })}
                    />
                  </div>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveRule} disabled={saving}>
                {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {editingRule ? "Update Rule" : "Create Rule"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Bell className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{rules.length}</p>
                <p className="text-sm text-muted-foreground">Active Rules</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <Activity className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{rules.filter(r => r.is_enabled).length}</p>
                <p className="text-sm text-muted-foreground">Enabled</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{rules.filter(r => r.urgency_level === 'high' || r.urgency_level === 'critical').length}</p>
                <p className="text-sm text-muted-foreground">High Priority</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{rules.reduce((sum, r) => sum + r.trigger_count, 0)}</p>
                <p className="text-sm text-muted-foreground">Total Triggers</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rules by Category */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Rules</TabsTrigger>
          {ruleCategories.map((cat) => (
            <TabsTrigger key={cat.id} value={cat.id}>
              {cat.name}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : rules.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bell className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">No notification rules yet</p>
                <p className="text-sm text-muted-foreground mb-4">Create your first rule to get started</p>
                <Button onClick={() => setDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Rule
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => {
                const category = getCategoryInfo(rule.rule_type);
                const indicator = getIndicatorInfo(rule.rule_type, rule.indicator_type);
                const urgency = urgencyOptions.find(u => u.value === rule.urgency_level);

                return (
                  <Card key={rule.id} className={!rule.is_enabled ? "opacity-60" : ""}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            {category && <category.icon className="h-5 w-5 text-primary" />}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium">{rule.rule_name}</h3>
                              <Badge variant="outline" className={urgency?.color}>
                                {urgency?.label}
                              </Badge>
                              {rule.frequency !== "immediate" && (
                                <Badge variant="secondary">{rule.frequency}</Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {indicator?.name} • Threshold: ${rule.conditions?.threshold || 0}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={rule.is_enabled}
                            onCheckedChange={() => handleToggleRule(rule)}
                          />
                          <Button variant="ghost" size="icon" onClick={() => handleEditRule(rule)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDeleteRule(rule.id)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {ruleCategories.map((cat) => (
          <TabsContent key={cat.id} value={cat.id} className="space-y-4">
            {rules.filter(r => r.rule_type === cat.id).length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <cat.icon className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium">No {cat.name.toLowerCase()} rules</p>
                  <p className="text-sm text-muted-foreground mb-4">{cat.description}</p>
                  <Button onClick={() => {
                    setFormData({ ...formData, rule_type: cat.id });
                    setDialogOpen(true);
                  }}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create {cat.name} Rule
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {rules.filter(r => r.rule_type === cat.id).map((rule) => {
                  const indicator = getIndicatorInfo(rule.rule_type, rule.indicator_type);
                  const urgency = urgencyOptions.find(u => u.value === rule.urgency_level);

                  return (
                    <Card key={rule.id} className={!rule.is_enabled ? "opacity-60" : ""}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between gap-4">
                          <div className="flex items-center gap-4 flex-1">
                            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                              <cat.icon className="h-5 w-5 text-primary" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium">{rule.rule_name}</h3>
                                <Badge variant="outline" className={urgency?.color}>
                                  {urgency?.label}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {indicator?.name} • Threshold: ${rule.conditions?.threshold || 0}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={rule.is_enabled}
                              onCheckedChange={() => handleToggleRule(rule)}
                            />
                            <Button variant="ghost" size="icon" onClick={() => handleEditRule(rule)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleDeleteRule(rule.id)}>
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
