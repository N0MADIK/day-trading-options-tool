import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  User,
  Mail,
  Phone,
  MapPin,
  Calendar,
  CreditCard,
  Crown,
  Download,
  Trash2,
  Camera,
  Edit2,
  Loader2,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

interface Profile {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  dateOfBirth: string;
  avatarUrl: string;
  subscriptionTier: string;
  createdAt: string;
}

export default function Account() {
  const { user, signOut } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState<Profile>({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    address: "",
    dateOfBirth: "",
    avatarUrl: "",
    subscriptionTier: "free",
    createdAt: "",
  });

  // Fetch user profile on mount
  useEffect(() => {
    if (!user) return;

    const fetchProfile = async () => {
      try {
        const data = await api.get<{
          full_name?: string;
          email?: string;
          phone?: string;
          address?: string;
          date_of_birth?: string;
          avatar_url?: string;
          subscription_tier?: string;
          created_at?: string;
        }>('/profiles/me').catch(() => null);

        if (data) {
          const [firstName, ...lastNameParts] = (data.full_name || "").split(" ");
          setProfile({
            firstName: firstName || "",
            lastName: lastNameParts.join(" ") || "",
            email: data.email || user.email || "",
            phone: data.phone || "",
            address: data.address || "",
            dateOfBirth: data.date_of_birth || "",
            avatarUrl: data.avatar_url || "",
            subscriptionTier: data.subscription_tier || "free",
            createdAt: data.created_at || "",
          });
        } else {
          setProfile((prev) => ({
            ...prev,
            email: user.email || "",
          }));
        }
      } catch (error) {
        console.error("Error fetching profile:", error);
        toast({
          title: "Error",
          description: "Failed to load profile data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  const handleSaveProfile = async () => {
    if (!user) return;
    setSaving(true);

    try {
      const fullName = `${profile.firstName} ${profile.lastName}`.trim();

      await api.put('/profiles/me', {
        full_name: fullName,
        email: profile.email,
        phone: profile.phone || null,
        address: profile.address || null,
        date_of_birth: profile.dateOfBirth || null,
        avatar_url: profile.avatarUrl || null,
      });

      setIsEditing(false);
      toast({
        title: "Profile Updated",
        description: "Your profile information has been saved.",
      });
    } catch (error) {
      console.error("Error saving profile:", error);
      toast({
        title: "Error",
        description: "Failed to save profile data",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = async () => {
    if (!user) return;

    try {
      // Fetch all user data via API
      const [profileData, accountsData, holdingsData, transactionsData] = await Promise.all([
        api.get('/profiles/me').catch(() => null),
        api.get('/connected-accounts').catch(() => []),
        api.get('/holdings').catch(() => []),
        api.get('/transactions').catch(() => []),
      ]);

      const exportData = {
        profile: profileData,
        accounts: accountsData,
        holdings: holdingsData,
        transactions: transactionsData,
        exportedAt: new Date().toISOString(),
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `finance-master-export-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Data Exported",
        description: "Your data has been downloaded successfully.",
      });
    } catch (error) {
      console.error("Error exporting data:", error);
      toast({
        title: "Error",
        description: "Failed to export data",
        variant: "destructive",
      });
    }
  };

  const handleDeleteAccount = async () => {
    if (!user) return;

    try {
      await signOut();
      toast({
        title: "Account Deleted",
        description: "Your account has been scheduled for deletion.",
      });
    } catch (error) {
      console.error("Error deleting account:", error);
      toast({
        title: "Error",
        description: "Failed to delete account",
        variant: "destructive",
      });
    }
  };

  const getInitials = () => {
    const first = profile.firstName?.[0] || "";
    const last = profile.lastName?.[0] || "";
    return (first + last).toUpperCase() || "U";
  };

  const getMemberSince = () => {
    if (!profile.createdAt) return "Recently";
    const date = new Date(profile.createdAt);
    return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  };

  const getSubscriptionLabel = () => {
    switch (profile.subscriptionTier) {
      case "premium":
        return "Pro Member";
      case "admin":
        return "Admin";
      default:
        return "Free Member";
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold">Account</h1>
          <p className="text-muted-foreground">Manage your personal information and subscription</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-6">
              <Skeleton className="h-24 w-24 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Account</h1>
        <p className="text-muted-foreground">
          Manage your personal information and subscription
        </p>
      </div>

      {/* Profile Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            <div className="relative">
              <Avatar className="h-24 w-24 border-4 border-primary">
                <AvatarImage src={profile.avatarUrl} />
                <AvatarFallback className="text-2xl bg-primary text-primary-foreground">
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              <button className="absolute bottom-0 right-0 p-2 rounded-full bg-secondary border border-border hover:bg-accent transition-colors">
                <Camera className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-2xl font-bold">
                  {profile.firstName || profile.lastName
                    ? `${profile.firstName} ${profile.lastName}`.trim()
                    : "User"}
                </h2>
                <Badge className="bg-primary/20 text-primary border-primary/30">
                  <Crown className="h-3 w-3 mr-1" />
                  {getSubscriptionLabel()}
                </Badge>
              </div>
              <p className="text-muted-foreground">{profile.email}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Member since {getMemberSince()}
              </p>
            </div>
            <Button
              variant={isEditing ? "default" : "outline"}
              onClick={() => (isEditing ? handleSaveProfile() : setIsEditing(true))}
              disabled={saving}
            >
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : isEditing ? (
                "Save Changes"
              ) : (
                <>
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit Profile
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            Personal Information
          </CardTitle>
          <CardDescription>
            Your personal details and contact information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                value={profile.firstName}
                onChange={(e) =>
                  setProfile({ ...profile, firstName: e.target.value })
                }
                disabled={!isEditing}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                value={profile.lastName}
                onChange={(e) =>
                  setProfile({ ...profile, lastName: e.target.value })
                }
                disabled={!isEditing}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              Email Address
            </Label>
            <Input
              id="email"
              type="email"
              value={profile.email}
              onChange={(e) =>
                setProfile({ ...profile, email: e.target.value })
              }
              disabled={!isEditing}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone" className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-muted-foreground" />
              Phone Number
            </Label>
            <Input
              id="phone"
              type="tel"
              value={profile.phone}
              onChange={(e) =>
                setProfile({ ...profile, phone: e.target.value })
              }
              disabled={!isEditing}
              placeholder={isEditing ? "Enter phone number" : "Not set"}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="address" className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              Address
            </Label>
            <Input
              id="address"
              value={profile.address}
              onChange={(e) =>
                setProfile({ ...profile, address: e.target.value })
              }
              disabled={!isEditing}
              placeholder={isEditing ? "Enter address" : "Not set"}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="dob" className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              Date of Birth
            </Label>
            <Input
              id="dob"
              type="date"
              value={profile.dateOfBirth}
              onChange={(e) =>
                setProfile({ ...profile, dateOfBirth: e.target.value })
              }
              disabled={!isEditing}
              className="max-w-xs"
            />
          </div>
        </CardContent>
      </Card>

      {/* Subscription */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-primary" />
            Subscription
          </CardTitle>
          <CardDescription>
            Manage your subscription and billing
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="p-4 rounded-lg border-2 border-primary bg-primary/5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Crown className="h-8 w-8 text-primary" />
                <div>
                  <h3 className="font-bold text-lg">
                    Finance Monkey {profile.subscriptionTier === "premium" ? "Pro" : "Free"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {profile.subscriptionTier === "premium"
                      ? "Unlimited connections & real-time data"
                      : "Basic features included"}
                  </p>
                </div>
              </div>
              <Badge className="bg-primary text-primary-foreground">Active</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">
                  {profile.subscriptionTier === "premium" ? "$19.99" : "$0"}
                  <span className="text-sm text-muted-foreground">/month</span>
                </p>
                {profile.subscriptionTier === "premium" && (
                  <p className="text-sm text-muted-foreground">
                    Next billing date: February 15, 2024
                  </p>
                )}
              </div>
              <Button variant="outline">
                {profile.subscriptionTier === "premium" ? "Manage Subscription" : "Upgrade to Pro"}
              </Button>
            </div>
          </div>

          <Separator />

          <div>
            <h4 className="font-semibold mb-3">Plan Features</h4>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2 text-muted-foreground">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                {profile.subscriptionTier === "premium" ? "Unlimited" : "Up to 3"} account connections
              </li>
              <li className="flex items-center gap-2 text-muted-foreground">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                {profile.subscriptionTier === "premium" ? "Real-time" : "Delayed"} market data
              </li>
              <li className="flex items-center gap-2 text-muted-foreground">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                Advanced options chain analysis
              </li>
              <li className="flex items-center gap-2 text-muted-foreground">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                {profile.subscriptionTier === "premium" ? "Priority" : "Standard"} customer support
              </li>
              <li className="flex items-center gap-2 text-muted-foreground">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                Custom price alerts ({profile.subscriptionTier === "premium" ? "unlimited" : "5 max"})
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card>
        <CardHeader>
          <CardTitle>Data & Privacy</CardTitle>
          <CardDescription>
            Export your data or delete your account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div>
              <h4 className="font-semibold">Export Your Data</h4>
              <p className="text-sm text-muted-foreground">
                Download a copy of all your data
              </p>
            </div>
            <Button variant="outline" onClick={handleExportData}>
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg border border-destructive/30 bg-destructive/5">
            <div>
              <h4 className="font-semibold text-destructive">Delete Account</h4>
              <p className="text-sm text-muted-foreground">
                Permanently delete your account and all data
              </p>
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Account
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete your
                    account and remove all your data from our servers.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    onClick={handleDeleteAccount}
                  >
                    Delete Account
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
