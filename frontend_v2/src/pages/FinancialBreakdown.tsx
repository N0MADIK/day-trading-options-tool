import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
import { useConnections } from "@/hooks/useConnections";
import { useMockData, MOCK_DATA } from "@/hooks/useMockData";
import { supabase } from "@/integrations/supabase/client";
import { DataPlaceholder } from "@/components/ui/DataPlaceholder";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from "recharts";
import {
  Target,
  TrendingUp,
  TrendingDown,
  Bell,
  DollarSign,
  Building,
  Briefcase,
  PiggyBank,
  AlertCircle,
  CheckCircle,
  ArrowUp,
  ArrowDown,
  ShoppingCart,
  Coffee,
  Car,
  Home,
  Utensils,
  Film,
  Repeat,
  ExternalLink,
  CreditCard,
  BarChart3,
  LineChart,
  PieChartIcon,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function FinancialBreakdown() {
  const { toast } = useToast();
  const { user } = useAuth();
  const { accounts, holdings, transactions, totalNetWorth, loading } = useConnections();
  const { showMockData } = useMockData();
  
  const [goalAmount, setGoalAmount] = useState("500000");
  const [goalDate, setGoalDate] = useState("2030-12-31");
  const [notifyOnProgress, setNotifyOnProgress] = useState(true);
  const [notifyThreshold, setNotifyThreshold] = useState("5");
  const [isGoalDialogOpen, setIsGoalDialogOpen] = useState(false);
  const [spendingChartType, setSpendingChartType] = useState<"pie" | "bar" | "line">("pie");
  const [spendingTimeframe, setSpendingTimeframe] = useState("month");
  const [netWorthGoal, setNetWorthGoal] = useState<any>(null);

  // Check for credit card accounts
  const hasCreditCardAccount = showMockData 
    ? true 
    : accounts.some(acc => acc.institution_type === 'credit_card' || acc.institution_type === 'credit');

  // Use mock data if toggle is on
  const hasConnectedAccounts = showMockData || accounts.length > 0;
  const hasHoldings = showMockData || holdings.length > 0;
  const hasTransactions = showMockData || transactions.length > 0;
  const displayNetWorth = showMockData ? MOCK_DATA.totalNetWorth : totalNetWorth;

  // Fetch net worth goal from database
  useEffect(() => {
    if (!user) return;
    
    const fetchGoal = async () => {
      const { data } = await supabase
        .from('net_worth_goals')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle();
      
      if (data) {
        setNetWorthGoal(data);
        setGoalAmount(data.target_amount.toString());
        setGoalDate(data.target_date?.split('T')[0] || '2030-12-31');
        setNotifyOnProgress(data.notify_on_progress || true);
        setNotifyThreshold((data.notify_threshold_percent || 5).toString());
      }
    };
    
    fetchGoal();
  }, [user]);

  // Account breakdown (mock or real)
  const accountBreakdown = showMockData 
    ? MOCK_DATA.accountBreakdown
    : accounts.map((acc, idx) => {
        const colors = [
          "hsl(142, 71%, 45%)",
          "hsl(173, 58%, 39%)",
          "hsl(197, 37%, 24%)",
          "hsl(38, 92%, 50%)",
          "hsl(280, 60%, 50%)",
          "hsl(0, 72%, 51%)",
        ];
        return {
          name: acc.institution_name,
          value: Math.abs(acc.balance || 0),
          type: acc.institution_type,
          color: colors[idx % colors.length],
        };
      });

  // Spending by category (mock or real) - improved categorization
  const spendingByCategory = showMockData 
    ? MOCK_DATA.spendingByCategory
    : (() => {
        if (transactions.length === 0) return [];
        
        // Define category mapping based on keywords
        const categoryKeywords: Record<string, { keywords: string[]; color: string; icon: string }> = {
          "Subscriptions": { keywords: ["netflix", "spotify", "amazon prime", "adobe", "openai", "chatgpt", "youtube premium", "icloud", "hulu", "disney"], color: "hsl(262, 83%, 58%)", icon: "subscription" },
          "Housing": { keywords: ["rent", "mortgage", "hoa", "property"], color: "hsl(220, 70%, 50%)", icon: "home" },
          "Food": { keywords: ["whole foods", "trader joe", "grocery", "safeway", "kroger", "restaurant", "doordash", "uber eats", "grubhub", "chipotle", "mcdonald"], color: "hsl(38, 92%, 50%)", icon: "food" },
          "Transportation": { keywords: ["gas", "shell", "chevron", "uber", "lyft", "parking", "toll"], color: "hsl(280, 60%, 50%)", icon: "car" },
          "Shopping": { keywords: ["amazon", "target", "walmart", "costco", "best buy", "apple store"], color: "hsl(142, 71%, 45%)", icon: "shopping" },
          "Entertainment": { keywords: ["movie", "theater", "concert", "ticket", "game"], color: "hsl(0, 72%, 51%)", icon: "entertainment" },
          "Utilities": { keywords: ["electric", "water", "gas bill", "internet", "phone", "verizon", "att", "comcast"], color: "hsl(173, 58%, 39%)", icon: "utilities" },
          "Coffee": { keywords: ["starbucks", "dunkin", "coffee", "cafe"], color: "hsl(25, 95%, 53%)", icon: "coffee" },
        };
        
        const categoryMap: Record<string, { amount: number; count: number; color: string; icon: string }> = {};
        
        transactions
          .filter(t => t.transaction_type === 'withdrawal' || t.transaction_type === 'expense' || t.total_amount < 0)
          .forEach((t) => {
            const description = (t.description || '').toLowerCase();
            let matchedCategory = 'Other';
            let matchedData = { color: "hsl(220, 15%, 50%)", icon: "other" };
            
            for (const [category, data] of Object.entries(categoryKeywords)) {
              if (data.keywords.some(keyword => description.includes(keyword))) {
                matchedCategory = category;
                matchedData = data;
                break;
              }
            }
            
            if (!categoryMap[matchedCategory]) {
              categoryMap[matchedCategory] = { amount: 0, count: 0, color: matchedData.color, icon: matchedData.icon };
            }
            categoryMap[matchedCategory].amount += Math.abs(t.total_amount);
            categoryMap[matchedCategory].count += 1;
          });
        
        return Object.entries(categoryMap)
          .map(([category, data]) => ({ category, ...data }))
          .sort((a, b) => b.amount - a.amount)
          .slice(0, 8);
      })();

  // Subscriptions (mock or detected from transactions)
  const subscriptions = showMockData 
    ? MOCK_DATA.subscriptions
    : (() => {
        if (transactions.length === 0) return [];
        
        // Common subscription services to detect
        const knownSubscriptions: Record<string, { website: string; logo: string; category: string }> = {
          "netflix": { website: "https://netflix.com", logo: "🎬", category: "Entertainment" },
          "spotify": { website: "https://spotify.com", logo: "🎵", category: "Entertainment" },
          "amazon prime": { website: "https://amazon.com/prime", logo: "📦", category: "Shopping" },
          "adobe": { website: "https://adobe.com", logo: "🎨", category: "Software" },
          "openai": { website: "https://openai.com", logo: "🤖", category: "Software" },
          "chatgpt": { website: "https://openai.com", logo: "🤖", category: "Software" },
          "youtube premium": { website: "https://youtube.com/premium", logo: "▶️", category: "Entertainment" },
          "icloud": { website: "https://icloud.com", logo: "☁️", category: "Cloud Storage" },
          "hulu": { website: "https://hulu.com", logo: "📺", category: "Entertainment" },
          "disney": { website: "https://disneyplus.com", logo: "🏰", category: "Entertainment" },
          "apple music": { website: "https://music.apple.com", logo: "🎵", category: "Entertainment" },
          "dropbox": { website: "https://dropbox.com", logo: "📁", category: "Cloud Storage" },
          "microsoft 365": { website: "https://microsoft.com", logo: "💼", category: "Software" },
          "gym": { website: "#", logo: "🏋️", category: "Health" },
          "planet fitness": { website: "https://planetfitness.com", logo: "🏋️", category: "Health" },
        };
        
        const detected: typeof MOCK_DATA.subscriptions = [];
        const seenVendors = new Set<string>();
        
        transactions
          .filter(t => t.total_amount < 0)
          .forEach(t => {
            const description = (t.description || '').toLowerCase();
            
            for (const [keyword, data] of Object.entries(knownSubscriptions)) {
              if (description.includes(keyword) && !seenVendors.has(keyword)) {
                seenVendors.add(keyword);
                detected.push({
                  id: t.id,
                  name: keyword.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
                  amount: Math.abs(t.total_amount),
                  billingCycle: "monthly",
                  category: data.category,
                  lastCharge: t.transaction_date,
                  website: data.website,
                  logo: data.logo,
                });
                break;
              }
            }
          });
        
        return detected;
      })();

  // Frequent vendors from transactions
  const frequentVendors = showMockData 
    ? MOCK_DATA.frequentVendors
    : (() => {
        if (transactions.length === 0) return [];
        
        const vendorMap: Record<string, { count: number; totalSpent: number }> = {};
        
        transactions
          .filter(t => t.total_amount < 0)
          .forEach(t => {
            const vendor = t.description?.split(' ')[0] || 'Unknown';
            if (!vendorMap[vendor]) {
              vendorMap[vendor] = { count: 0, totalSpent: 0 };
            }
            vendorMap[vendor].count += 1;
            vendorMap[vendor].totalSpent += Math.abs(t.total_amount);
          });
        
        return Object.entries(vendorMap)
          .map(([name, data]) => ({ 
            name, 
            count: data.count, 
            totalSpent: data.totalSpent, 
            avgTransaction: data.totalSpent / data.count 
          }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);
      })();

  // Year-over-year spending comparison data
  const yearOverYearSpending = showMockData 
    ? MOCK_DATA.yearOverYearSpending
    : (() => {
        if (transactions.length === 0) return [];
        
        const currentYear = new Date().getFullYear();
        const previousYear = currentYear - 1;
        
        const monthlyData: Record<number, { currentYear: number; previousYear: number }> = {};
        
        // Initialize all months
        for (let i = 0; i < 12; i++) {
          monthlyData[i] = { currentYear: 0, previousYear: 0 };
        }
        
        transactions
          .filter(t => t.total_amount < 0)
          .forEach(t => {
            const date = new Date(t.transaction_date);
            const year = date.getFullYear();
            const month = date.getMonth();
            
            if (year === currentYear) {
              monthlyData[month].currentYear += Math.abs(t.total_amount);
            } else if (year === previousYear) {
              monthlyData[month].previousYear += Math.abs(t.total_amount);
            }
          });
        
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        return months.map((month, idx) => ({
          month,
          currentYear: Math.round(monthlyData[idx].currentYear),
          previousYear: Math.round(monthlyData[idx].previousYear),
          percentChange: monthlyData[idx].previousYear > 0 
            ? ((monthlyData[idx].currentYear - monthlyData[idx].previousYear) / monthlyData[idx].previousYear) * 100
            : 0,
        }));
      })();

  // Category YoY comparison
  const categoryYoYComparison = showMockData 
    ? MOCK_DATA.categoryYoYComparison
    : [];

  // Net worth history (mock or real)
  const netWorthHistory = showMockData 
    ? MOCK_DATA.netWorthHistory
    : (() => {
        if (accounts.length === 0) return [];
        
        const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const baseValue = totalNetWorth * 0.7;
        const growth = (totalNetWorth - baseValue) / 6;
        
        return months.map((month, idx) => ({
          month,
          netWorth: Math.round(baseValue + growth * idx),
          assets: Math.round((baseValue + growth * idx) * 1.1),
          liabilities: Math.round((baseValue + growth * idx) * 0.1),
        }));
      })();

  // Recent transactions (mock or real)
  const recentTransactions = showMockData 
    ? MOCK_DATA.recentTransactions
    : (transactions.length > 0
        ? transactions.slice(0, 5).map(tx => ({
            id: tx.id,
            type: tx.transaction_type,
            symbol: tx.symbol,
            amount: tx.total_amount,
            date: new Date(tx.transaction_date).toLocaleDateString(),
            account: accounts.find(a => a.id === tx.account_id)?.institution_name || 'Unknown',
            vendor: tx.description,
          }))
        : []);

  const currentNetWorth = displayNetWorth;
  const targetNetWorth = parseFloat(goalAmount) || 500000;
  const progressPercent = hasConnectedAccounts ? Math.min((currentNetWorth / targetNetWorth) * 100, 100) : 0;
  const amountRemaining = targetNetWorth - currentNetWorth;

  // P&L (mock or real)
  const totalPnL = showMockData ? MOCK_DATA.totalPnL : holdings.reduce((sum, h) => sum + (h.unrealized_pnl || 0), 0);
  const totalPnLPercent = showMockData 
    ? MOCK_DATA.totalPnLPercent 
    : (holdings.length > 0 
        ? holdings.reduce((sum, h) => sum + (h.unrealized_pnl_percent || 0), 0) / holdings.length 
        : 0);

  const totalSpending = showMockData ? MOCK_DATA.totalSpending : spendingByCategory.reduce((sum, cat) => sum + cat.amount, 0);
  const totalSubscriptionCost = subscriptions.reduce((sum, sub) => sum + sub.amount, 0);

  const handleSaveGoal = async () => {
    if (!user) return;

    try {
      const goalData = {
        user_id: user.id,
        target_amount: parseFloat(goalAmount),
        target_date: goalDate,
        notify_on_progress: notifyOnProgress,
        notify_threshold_percent: parseFloat(notifyThreshold),
      };

      if (netWorthGoal) {
        await supabase
          .from('net_worth_goals')
          .update(goalData)
          .eq('id', netWorthGoal.id);
      } else {
        const { data } = await supabase
          .from('net_worth_goals')
          .insert(goalData)
          .select()
          .single();
        setNetWorthGoal(data);
      }

      toast({
        title: "Goal Updated",
        description: `Your net worth goal has been set to $${parseFloat(goalAmount).toLocaleString()}`,
      });
      setIsGoalDialogOpen(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save goal",
        variant: "destructive",
      });
    }
  };

  const getAccountIcon = (type: string) => {
    switch (type) {
      case "bank":
        return <Building className="h-4 w-4" />;
      case "investment":
      case "brokerage":
        return <TrendingUp className="h-4 w-4" />;
      case "retirement":
        return <PiggyBank className="h-4 w-4" />;
      case "credit_card":
      case "credit":
        return <CreditCard className="h-4 w-4" />;
      default:
        return <Briefcase className="h-4 w-4" />;
    }
  };

  const getCategoryIcon = (icon: string) => {
    switch (icon) {
      case "home":
        return <Home className="h-4 w-4" />;
      case "food":
        return <Utensils className="h-4 w-4" />;
      case "car":
        return <Car className="h-4 w-4" />;
      case "shopping":
        return <ShoppingCart className="h-4 w-4" />;
      case "entertainment":
        return <Film className="h-4 w-4" />;
      case "utilities":
        return <Building className="h-4 w-4" />;
      case "coffee":
        return <Coffee className="h-4 w-4" />;
      case "subscription":
        return <Repeat className="h-4 w-4" />;
      default:
        return <DollarSign className="h-4 w-4" />;
    }
  };

  const renderSpendingChart = () => {
    if (!hasTransactions || spendingByCategory.length === 0) {
      return (
        <DataPlaceholder
          title="No Spending Data"
          description="Connect a bank or credit card account to see spending analysis"
          className="h-[300px]"
        />
      );
    }

    switch (spendingChartType) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={spendingByCategory} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
              <XAxis type="number" stroke="hsl(220, 10%, 55%)" fontSize={12} tickFormatter={(value) => `$${value}`} />
              <YAxis type="category" dataKey="category" stroke="hsl(220, 10%, 55%)" fontSize={12} width={100} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(220, 18%, 10%)",
                  border: "1px solid hsl(220, 15%, 20%)",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, "Amount"]}
              />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                {spendingByCategory.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );
      case "line":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={spendingByCategory}>
              <defs>
                <linearGradient id="spendingGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(220, 70%, 50%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(220, 70%, 50%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
              <XAxis dataKey="category" stroke="hsl(220, 10%, 55%)" fontSize={10} angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="hsl(220, 10%, 55%)" fontSize={12} tickFormatter={(value) => `$${value}`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(220, 18%, 10%)",
                  border: "1px solid hsl(220, 15%, 20%)",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, "Amount"]}
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="hsl(220, 70%, 50%)"
                fill="url(#spendingGradient)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        );
      case "pie":
      default:
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={spendingByCategory}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="amount"
                label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {spendingByCategory.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(220, 18%, 10%)",
                  border: "1px solid hsl(220, 15%, 20%)",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
              />
            </PieChart>
          </ResponsiveContainer>
        );
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[400px]" />
          <Skeleton className="h-[400px]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Financial Breakdown</h1>
          <p className="text-muted-foreground">Deep dive into your complete financial picture</p>
        </div>
        <Dialog open={isGoalDialogOpen} onOpenChange={setIsGoalDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Target className="h-4 w-4 mr-2" />
              Set Net Worth Goal
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Set Your Net Worth Goal</DialogTitle>
              <DialogDescription>
                Define your target net worth and receive notifications as you make progress.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="goal-amount">Target Net Worth ($)</Label>
                <Input
                  id="goal-amount"
                  type="number"
                  value={goalAmount}
                  onChange={(e) => setGoalAmount(e.target.value)}
                  placeholder="500000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="goal-date">Target Date</Label>
                <Input
                  id="goal-date"
                  type="date"
                  value={goalDate}
                  onChange={(e) => setGoalDate(e.target.value)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Progress Notifications</Label>
                  <p className="text-sm text-muted-foreground">Get notified as you approach your goal</p>
                </div>
                <Switch
                  checked={notifyOnProgress}
                  onCheckedChange={setNotifyOnProgress}
                />
              </div>
              {notifyOnProgress && (
                <div className="space-y-2">
                  <Label htmlFor="notify-threshold">Notify every (% change)</Label>
                  <Input
                    id="notify-threshold"
                    type="number"
                    value={notifyThreshold}
                    onChange={(e) => setNotifyThreshold(e.target.value)}
                    placeholder="5"
                  />
                </div>
              )}
              <Button onClick={handleSaveGoal} className="w-full">
                Save Goal
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Net Worth Goal Progress */}
      <Card className="border-border bg-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-primary" />
                Net Worth Goal Progress
              </CardTitle>
              <CardDescription>Track your journey to financial independence</CardDescription>
            </div>
            {hasConnectedAccounts && progressPercent >= 75 ? (
              <Badge variant="default" className="bg-primary text-primary-foreground">
                <CheckCircle className="h-3 w-3 mr-1" />
                On Track
              </Badge>
            ) : hasConnectedAccounts ? (
              <Badge variant="secondary">
                <AlertCircle className="h-3 w-3 mr-1" />
                Keep Going
              </Badge>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasConnectedAccounts ? (
            <>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Current Net Worth</p>
                  <p className="text-3xl font-bold text-foreground">${currentNetWorth.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Target</p>
                  <p className="text-xl font-semibold text-muted-foreground">${targetNetWorth.toLocaleString()}</p>
                </div>
              </div>
              <Progress value={progressPercent} className="h-3" />
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{progressPercent.toFixed(1)}% complete</span>
                <span className="text-muted-foreground">${amountRemaining.toLocaleString()} remaining</span>
              </div>
            </>
          ) : (
            <DataPlaceholder
              title="No Accounts Connected"
              description="Connect your financial accounts to track your net worth progress"
              className="min-h-[150px]"
            />
          )}
        </CardContent>
      </Card>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            {hasConnectedAccounts ? (
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <DollarSign className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Assets</p>
                  <p className="text-xl font-bold text-foreground">${totalNetWorth.toLocaleString()}</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 opacity-50">
                <div className="p-2 rounded-lg bg-muted">
                  <DollarSign className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Assets</p>
                  <p className="text-xl font-bold text-muted-foreground">$0</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-destructive/10">
                <TrendingDown className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Liabilities</p>
                <p className="text-xl font-bold text-foreground">$0</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            {hasHoldings ? (
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total P&L</p>
                  <p className={`text-xl font-bold ${totalPnL >= 0 ? 'text-primary' : 'text-destructive'}`}>
                    {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString()}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 opacity-50">
                <div className="p-2 rounded-lg bg-muted">
                  <TrendingUp className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total P&L</p>
                  <p className="text-xl font-bold text-muted-foreground">$0</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            {hasHoldings ? (
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <ArrowUp className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">ROI</p>
                  <p className={`text-xl font-bold ${totalPnLPercent >= 0 ? 'text-primary' : 'text-destructive'}`}>
                    {totalPnLPercent >= 0 ? '+' : ''}{totalPnLPercent.toFixed(1)}%
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 opacity-50">
                <div className="p-2 rounded-lg bg-muted">
                  <ArrowUp className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">ROI</p>
                  <p className="text-xl font-bold text-muted-foreground">0%</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Net Worth Over Time */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Net Worth Over Time</CardTitle>
            <CardDescription>Track your wealth growth month by month</CardDescription>
          </CardHeader>
          <CardContent>
            {hasConnectedAccounts ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={netWorthHistory}>
                  <defs>
                    <linearGradient id="netWorthGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
                  <XAxis dataKey="month" stroke="hsl(220, 10%, 55%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 55%)" fontSize={12} tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(220, 18%, 10%)",
                      border: "1px solid hsl(220, 15%, 20%)",
                      borderRadius: "8px",
                    }}
                    formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
                  />
                  <Area
                    type="monotone"
                    dataKey="netWorth"
                    stroke="hsl(142, 71%, 45%)"
                    fill="url(#netWorthGradient)"
                    strokeWidth={2}
                    name="Net Worth"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <DataPlaceholder
                title="No Data Available"
                description="Connect accounts to see your net worth history"
                className="h-[300px]"
              />
            )}
          </CardContent>
        </Card>

        {/* Asset Allocation */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Asset Allocation</CardTitle>
            <CardDescription>Breakdown by account type</CardDescription>
          </CardHeader>
          <CardContent>
            {hasConnectedAccounts && accountBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={accountBreakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {accountBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(220, 18%, 10%)",
                      border: "1px solid hsl(220, 15%, 20%)",
                      borderRadius: "8px",
                    }}
                    formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <DataPlaceholder
                title="No Accounts Connected"
                description="Connect your accounts to see asset allocation"
                className="h-[300px]"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Spending Breakdown Section */}
      <Card className="border-border bg-card">
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" />
                Spending Breakdown
              </CardTitle>
              <CardDescription>Categorized spending from bank & credit card accounts</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Tabs value={spendingTimeframe} onValueChange={setSpendingTimeframe}>
                <TabsList className="h-8">
                  <TabsTrigger value="week" className="text-xs px-2">Week</TabsTrigger>
                  <TabsTrigger value="month" className="text-xs px-2">Month</TabsTrigger>
                  <TabsTrigger value="year" className="text-xs px-2">Year</TabsTrigger>
                </TabsList>
              </Tabs>
              <div className="flex items-center gap-1 border border-border rounded-lg p-1">
                <Button
                  variant={spendingChartType === "pie" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setSpendingChartType("pie")}
                >
                  <PieChartIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant={spendingChartType === "bar" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setSpendingChartType("bar")}
                >
                  <BarChart3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={spendingChartType === "line" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setSpendingChartType("line")}
                >
                  <LineChart className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Chart */}
            <div>
              {renderSpendingChart()}
              {hasTransactions && spendingByCategory.length > 0 && (
                <div className="mt-4 text-center">
                  <p className="text-sm text-muted-foreground">Total Spending</p>
                  <p className="text-2xl font-bold text-foreground">${totalSpending.toLocaleString()}</p>
                </div>
              )}
            </div>
            
            {/* Category breakdown list */}
            <div className="space-y-3">
              <h4 className="font-medium text-foreground">By Category</h4>
              {spendingByCategory.length > 0 ? (
                spendingByCategory.map((cat, index) => (
                  <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg" style={{ backgroundColor: `${cat.color}20` }}>
                        {getCategoryIcon(cat.icon)}
                      </div>
                      <div>
                        <p className="font-medium text-foreground text-sm">{cat.category}</p>
                        <p className="text-xs text-muted-foreground">{cat.count} transactions</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-foreground">${cat.amount.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">{((cat.amount / totalSpending) * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <CreditCard className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No spending data available</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Scanner Section */}
      <Card className="border-border bg-card">
        <CardHeader>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Repeat className="h-5 w-5 text-primary" />
                Subscription Scanner
              </CardTitle>
              <CardDescription>
                {hasCreditCardAccount 
                  ? "Detected recurring payments from your connected accounts"
                  : "Connect a credit card to detect subscriptions"
                }
              </CardDescription>
            </div>
            {subscriptions.length > 0 && (
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Monthly Total</p>
                <p className="text-xl font-bold text-foreground">${totalSubscriptionCost.toFixed(2)}</p>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {hasCreditCardAccount && subscriptions.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {subscriptions.map((sub) => (
                <div key={sub.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 border border-border/50">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{sub.logo}</div>
                    <div>
                      <p className="font-medium text-foreground">{sub.name}</p>
                      <p className="text-xs text-muted-foreground">{sub.category}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <p className="font-semibold text-foreground">${sub.amount.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">/{sub.billingCycle}</p>
                    </div>
                    <a 
                      href={sub.website} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-md hover:bg-secondary transition-colors"
                    >
                      <ExternalLink className="h-4 w-4 text-muted-foreground" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <DataPlaceholder
              title={hasCreditCardAccount ? "No Subscriptions Detected" : "No Credit Card Connected"}
              description={hasCreditCardAccount 
                ? "We couldn't find any recurring payments in your transactions"
                : "Connect a credit card to automatically detect recurring subscriptions"
              }
              className="min-h-[200px]"
            />
          )}
        </CardContent>
      </Card>

      {/* Frequent Vendors Section */}
      {(hasCreditCardAccount || showMockData) && frequentVendors.length > 0 && (
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-primary" />
              Frequent Vendors
            </CardTitle>
            <CardDescription>Your most visited merchants this month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {frequentVendors.map((vendor, index) => (
                <div key={index} className="p-3 rounded-lg bg-secondary/50 border border-border/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium text-foreground truncate">{vendor.name}</p>
                    <Badge variant="secondary" className="text-xs">{vendor.count}x</Badge>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total</span>
                      <span className="text-foreground">${vendor.totalSpent.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Avg</span>
                      <span className="text-muted-foreground">${vendor.avgTransaction.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Year-over-Year Spending Comparison */}
      <Card className="border-border bg-card">
        <CardHeader>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Year-over-Year Spending
              </CardTitle>
              <CardDescription>Compare your spending habits across years</CardDescription>
            </div>
            {yearOverYearSpending.length > 0 && (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-primary" />
                  <span className="text-sm text-muted-foreground">{new Date().getFullYear()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "hsl(220, 15%, 50%)" }} />
                  <span className="text-sm text-muted-foreground">{new Date().getFullYear() - 1}</span>
                </div>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {hasTransactions && yearOverYearSpending.length > 0 ? (
            <div className="space-y-6">
              {/* Line Chart Comparison */}
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={yearOverYearSpending}>
                  <defs>
                    <linearGradient id="currentYearGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="previousYearGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(220, 15%, 50%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(220, 15%, 50%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 15%, 20%)" />
                  <XAxis dataKey="month" stroke="hsl(220, 10%, 55%)" fontSize={12} />
                  <YAxis stroke="hsl(220, 10%, 55%)" fontSize={12} tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(220, 18%, 10%)",
                      border: "1px solid hsl(220, 15%, 20%)",
                      borderRadius: "8px",
                    }}
                    formatter={(value: number, name: string) => [
                      `$${value.toLocaleString()}`,
                      name === "currentYear" ? new Date().getFullYear().toString() : (new Date().getFullYear() - 1).toString()
                    ]}
                  />
                  <Legend 
                    formatter={(value) => value === "currentYear" ? new Date().getFullYear() : new Date().getFullYear() - 1}
                  />
                  <Area
                    type="monotone"
                    dataKey="previousYear"
                    stroke="hsl(220, 15%, 50%)"
                    fill="url(#previousYearGradient)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="previousYear"
                  />
                  <Area
                    type="monotone"
                    dataKey="currentYear"
                    stroke="hsl(142, 71%, 45%)"
                    fill="url(#currentYearGradient)"
                    strokeWidth={2}
                    name="currentYear"
                  />
                </AreaChart>
              </ResponsiveContainer>

              {/* Monthly Comparison Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {yearOverYearSpending.slice(0, 12).map((data, index) => {
                  const isIncrease = data.percentChange > 0;
                  const isDecrease = data.percentChange < 0;
                  return (
                    <div key={index} className="p-3 rounded-lg bg-secondary/50 border border-border/50">
                      <p className="text-xs font-medium text-muted-foreground mb-1">{data.month}</p>
                      <p className="font-semibold text-foreground">${data.currentYear.toLocaleString()}</p>
                      <div className="flex items-center gap-1 mt-1">
                        {isIncrease ? (
                          <ArrowUpRight className="h-3 w-3 text-destructive" />
                        ) : isDecrease ? (
                          <ArrowDownRight className="h-3 w-3 text-primary" />
                        ) : null}
                        <span className={`text-xs ${isIncrease ? 'text-destructive' : isDecrease ? 'text-primary' : 'text-muted-foreground'}`}>
                          {data.percentChange !== 0 ? `${data.percentChange > 0 ? '+' : ''}${data.percentChange.toFixed(1)}%` : '-'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Category Comparison */}
              {categoryYoYComparison.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium text-foreground">Category Comparison</h4>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {categoryYoYComparison.map((cat, index) => {
                      const isIncrease = cat.percentChange > 0;
                      const isDecrease = cat.percentChange < 0;
                      return (
                        <div key={index} className="p-4 rounded-lg bg-secondary/50 border border-border/50">
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium text-foreground">{cat.category}</p>
                            <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full ${
                              isIncrease ? 'bg-destructive/10' : isDecrease ? 'bg-primary/10' : 'bg-muted'
                            }`}>
                              {isIncrease ? (
                                <ArrowUpRight className="h-3 w-3 text-destructive" />
                              ) : isDecrease ? (
                                <ArrowDownRight className="h-3 w-3 text-primary" />
                              ) : null}
                              <span className={`text-xs font-medium ${
                                isIncrease ? 'text-destructive' : isDecrease ? 'text-primary' : 'text-muted-foreground'
                              }`}>
                                {cat.percentChange > 0 ? '+' : ''}{cat.percentChange.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <p className="text-xs text-muted-foreground">{new Date().getFullYear()}</p>
                              <p className="font-semibold text-foreground">${cat.currentYear.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">{new Date().getFullYear() - 1}</p>
                              <p className="text-muted-foreground">${cat.previousYear.toLocaleString()}</p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <DataPlaceholder
              title="Not Enough Data"
              description="Connect accounts with at least one year of transactions to see year-over-year comparison"
              className="min-h-[350px]"
            />
          )}
        </CardContent>
      </Card>

      {/* Account Details & Recent Transactions */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Account Details */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>Breakdown by financial institution</CardDescription>
          </CardHeader>
          <CardContent>
            {hasConnectedAccounts ? (
              <div className="space-y-4">
                {accountBreakdown.map((account, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg" style={{ backgroundColor: `${account.color}20` }}>
                        {getAccountIcon(account.type)}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{account.name}</p>
                        <p className="text-sm text-muted-foreground capitalize">{account.type}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-foreground">${account.value.toLocaleString()}</p>
                      <p className="text-sm text-muted-foreground">
                        {totalNetWorth > 0 ? ((account.value / totalNetWorth) * 100).toFixed(1) : 0}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <DataPlaceholder
                title="No Accounts Connected"
                description="Connect your financial accounts to see the breakdown"
                className="min-h-[250px]"
              />
            )}
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Latest activity across all accounts</CardDescription>
          </CardHeader>
          <CardContent>
            {hasTransactions ? (
              <div className="space-y-3">
                {recentTransactions.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        tx.type === "buy" || tx.type === "deposit" 
                          ? "bg-primary/10" 
                          : tx.type === "sell" || tx.type === "withdrawal"
                          ? "bg-destructive/10"
                          : "bg-secondary"
                      }`}>
                        {tx.type === "buy" || tx.type === "deposit" ? (
                          <ArrowDown className="h-4 w-4 text-primary" />
                        ) : tx.type === "sell" || tx.type === "withdrawal" ? (
                          <ArrowUp className="h-4 w-4 text-destructive" />
                        ) : (
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-foreground capitalize">
                          {tx.type} {tx.symbol && <span className="text-primary">{tx.symbol}</span>}
                        </p>
                        <p className="text-sm text-muted-foreground">{tx.account}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${tx.amount >= 0 ? "text-primary" : "text-destructive"}`}>
                        {tx.amount >= 0 ? "+" : ""}${Math.abs(tx.amount).toLocaleString()}
                      </p>
                      <p className="text-sm text-muted-foreground">{tx.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <DataPlaceholder
                title="No Transactions"
                description="Import transactions via CSV or connect an account"
                className="min-h-[250px]"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Notification Settings */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Goal Notifications
          </CardTitle>
          <CardDescription>Configure when and how you receive progress updates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
              <div>
                <p className="font-medium text-foreground">Progress Milestones</p>
                <p className="text-sm text-muted-foreground">Get notified at 25%, 50%, 75%, and 100%</p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
              <div>
                <p className="font-medium text-foreground">Monthly Summary</p>
                <p className="text-sm text-muted-foreground">Receive a monthly net worth update</p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
              <div>
                <p className="font-medium text-foreground">Large Changes</p>
                <p className="text-sm text-muted-foreground">Alert for changes over 5%</p>
              </div>
              <Switch />
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
              <div>
                <p className="font-medium text-foreground">Goal Achieved</p>
                <p className="text-sm text-muted-foreground">Celebrate when you reach your goal</p>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
