import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { UserProvider } from "@/contexts/UserContext";
import { useAuth } from "@/hooks/useAuth";
import Index from "./pages/Index";
import { AuthPage } from "./pages/Auth";
import { OnboardingPage } from "./pages/Onboarding";
import { WorkoutsPage } from "./pages/Workouts";
import { CoachPage } from "./pages/Coach";
import { ProfilePage } from "./pages/Profile";
import { SchedulePage } from "./pages/Schedule";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  // إذا كان التحميل جارياً
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-muted-foreground text-sm">جاري التحميل...</p>
      </div>
    );
  }
  
  // إذا كان هناك مستخدم (حقيقي أو mock)
  if (user) {
    return <>{children}</>;
  }
  
  // إذا لم يكن هناك مستخدم، اعد التوجيه إلى Auth
  return <Navigate to="/auth" replace />;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <LanguageProvider>
      <UserProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
              <Route path="/workouts" element={<ProtectedRoute><WorkoutsPage /></ProtectedRoute>} />
              <Route path="/coach" element={<ProtectedRoute><CoachPage /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
              <Route path="/schedule" element={<ProtectedRoute><SchedulePage /></ProtectedRoute>} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </UserProvider>
    </LanguageProvider>
  </QueryClientProvider>
);

export default App;
