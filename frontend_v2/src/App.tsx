import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { MockDataProvider } from "./hooks/useMockData";
import { AppLayout } from "./components/layout/AppLayout";
import Index from "./pages/Index";
import Connections from "./pages/Connections";
import MarketScanner from "./pages/MarketScanner";
import Settings from "./pages/Settings";
import Account from "./pages/Account";
import Auth from "./pages/Auth";
import FinancialBreakdown from "./pages/FinancialBreakdown";
import PortfolioBreakdown from "./pages/PortfolioBreakdown";
import ProStrategizer from "./pages/ProStrategizer";
import AccountDetail from "./pages/AccountDetail";
import CustomNotifications from "./pages/CustomNotifications";
import AdminDashboard from "./pages/AdminDashboard";
import NotFound from "./pages/NotFound";
import { Loader2 } from "lucide-react";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  return <>{children}</>;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <AuthProvider>
        <MockDataProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <Routes>
                <Route path="/auth" element={<Auth />} />
                <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                  <Route path="/" element={<Index />} />
                  <Route path="/connections" element={<Connections />} />
                  <Route path="/account/:accountId" element={<AccountDetail />} />
                  <Route path="/scanner" element={<MarketScanner />} />
                  <Route path="/breakdown" element={<FinancialBreakdown />} />
                  <Route path="/portfolio" element={<PortfolioBreakdown />} />
                  <Route path="/strategizer" element={<ProStrategizer />} />
                  <Route path="/notifications" element={<CustomNotifications />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/account" element={<Account />} />
                  <Route path="/admin" element={<AdminDashboard />} />
                </Route>
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
          </TooltipProvider>
        </MockDataProvider>
      </AuthProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
