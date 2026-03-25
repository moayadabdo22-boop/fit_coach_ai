import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dumbbell, Mail, Lock, User, Eye, EyeOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useLanguage } from '@/contexts/LanguageContext';
import { supabase, isSupabaseConfigured } from '@/integrations/supabase/client';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';

export function AuthPage() {
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut } = useAuth();
  const { toast } = useToast();

  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [hasSession, setHasSession] = useState(false);
  const forceAuth = new URLSearchParams(location.search).get('force') === '1';
  const supabaseReady = isSupabaseConfigured();

  useEffect(() => {
    // ???????????? ???????????? ???? ???????????? ?????????????? (Supabase ???? Mock)
    let isMounted = true;
    const markSession = (exists: boolean) => {
      if (!isMounted) return;
      setHasSession(exists);
      if (exists && !forceAuth) {
        navigate('/', { replace: true });
      }
    };
    const readMockUser = () => {
      if (supabaseReady) return null;
      const memoryUser = (globalThis as any).__fitcoach_mock_user;
      const storedUser = localStorage.getItem('fitcoach_mock_user');
      if (!storedUser) return memoryUser || null;
      try {
        return JSON.parse(storedUser);
      } catch {
        localStorage.removeItem('fitcoach_mock_user');
        return memoryUser || null;
      }
    };

    try {
      // ???????? ???? Supabase availability
      if (supabaseReady && supabase && supabase.auth && supabase.auth.onAuthStateChange) {
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
          if (session?.user) {
            markSession(true);
          }
        });

        supabase.auth.getSession().then(({ data: { session } }) => {
          if (session?.user) {
            markSession(true);
          } else {
            markSession(false);
          }
        }).catch(() => {
          markSession(false);
        });

        return () => {
          isMounted = false;
          subscription?.unsubscribe?.();
        };
      } else {
        // Supabase not configured, just check localStorage
        const storedUser = readMockUser();
        markSession(Boolean(storedUser));
      }
    } catch {
      // ?????????? ??????????????
    }
    return () => {
      isMounted = false;
    };
  }, [navigate, forceAuth]);

  const handleSignOut = async () => {
    await signOut();
    setHasSession(false);
  };

  const handleMockAuth = async (isSigningUp: boolean) => {
    if (isSigningUp && !name) {
      toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: language === 'ar' ? 'من فضلك أدخل اسمك' : 'Please enter your name' });
      return;
    }

    const mockUser = {
      id: `user_${email.replace(/[^a-z0-9]/g, '')}_${Date.now()}`,
      email,
      user_metadata: { name, created_at: new Date().toISOString() },
    };

    try {
      localStorage.setItem('fitcoach_mock_user', JSON.stringify(mockUser));
    } catch {
      (globalThis as any).__fitcoach_mock_user = mockUser;
    }

    // Trigger storage event for other listeners
    window.dispatchEvent(new Event('storage'));

    toast({ title: language === 'ar' ? 'نجاح!' : 'Success!', description: language === 'ar' ? 'تم تسجيل الدخول بنجاح' : 'Signed in successfully' });

    // انتظر لضمان تحديث الـ user state
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // استدعي الانتقال
    navigate(isSigningUp ? '/onboarding' : '/', { replace: true });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);

    try {
      if (isLogin) {
        if (supabaseReady) {
          const { error } = await supabase.auth.signInWithPassword({ email, password });
          if (error) {
            toast({
              variant: 'destructive',
              title: language === 'ar' ? 'خطأ' : 'Error',
              description: language === 'ar' ? error.message : error.message,
            });
            return;
          }
          toast({
            title: language === 'ar' ? 'نجاح!' : 'Success!',
            description: language === 'ar' ? 'تم تسجيل الدخول بنجاح' : 'Signed in successfully',
          });
          navigate('/', { replace: true });
          return;
        }
        await handleMockAuth(false);
      } else {
        if (password.length < 6) {
          toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: language === 'ar' ? 'كلمة المرور يجب أن تكون 6 أحرف على الأقل' : 'Password must be at least 6 characters' });
          setLoading(false);
          return;
        }
        if (supabaseReady) {
          const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
              data: { name },
              emailRedirectTo: `${window.location.origin}/auth`,
            },
          });
          if (error) {
            toast({
              variant: 'destructive',
              title: language === 'ar' ? 'خطأ' : 'Error',
              description: language === 'ar' ? error.message : error.message,
            });
            return;
          }
          toast({
            title: language === 'ar' ? 'تم الإرسال' : 'Check your email',
            description: language === 'ar'
              ? 'تم إرسال رابط التفعيل لبريدك الإلكتروني. فعّل الحساب ثم سجّل الدخول.'
              : 'Confirmation link sent to your email. Verify your account then sign in.',
          });
          setIsLogin(true);
          return;
        }
        await handleMockAuth(true);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow">
            <Dumbbell className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="font-display text-4xl text-foreground">FITCOACH</h1>
          <p className="text-muted-foreground mt-2">
            {isLogin
              ? (language === 'ar' ? 'سجل دخولك للمتابعة' : 'Sign in to continue your journey')
              : (language === 'ar' ? 'أنشئ حسابك وابدأ رحلتك' : 'Create your account to get started')
            }
          </p>
        </div>

        {/* Form */}
        <div className="glass-card rounded-2xl p-8">
          {(hasSession || user) && (
            <div className="mb-6 rounded-xl border border-border/50 bg-secondary/30 p-4 text-sm">
              <p className="text-foreground">
                {language === 'ar' ? 'أنت مسجّل دخول الآن.' : 'You are currently signed in.'}
              </p>
              <div className="mt-3 flex flex-col sm:flex-row gap-2">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full sm:w-auto"
                  onClick={() => navigate('/')}
                >
                  {language === 'ar' ? 'العودة للرئيسية' : 'Continue'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full sm:w-auto"
                  onClick={handleSignOut}
                >
                  {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                </Button>
              </div>
            </div>
          )}
          {/* Tabs */}
          <div className="flex gap-2 mb-6 bg-secondary/30 p-1 rounded-lg">
            <Button
              type="button"
              variant={isLogin ? 'default' : 'ghost'}
              className="flex-1"
              onClick={() => setIsLogin(true)}
            >
              {language === 'ar' ? 'دخول' : 'Sign In'}
            </Button>
            <Button
              type="button"
              variant={!isLogin ? 'default' : 'ghost'}
              className="flex-1"
              onClick={() => setIsLogin(false)}
            >
              {language === 'ar' ? 'إنشاء حساب' : 'Sign Up'}
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <AnimatePresence mode="wait">
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder={language === 'ar' ? 'الاسم' : 'Full Name'}
                      className="pl-10 bg-secondary/50 border-border"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={language === 'ar' ? 'البريد الإلكتروني' : 'Email'}
                className="pl-10 bg-secondary/50 border-border"
                required
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={language === 'ar' ? 'كلمة المرور' : 'Password'}
                className="pl-10 pr-10 bg-secondary/50 border-border"
                required
                minLength={6}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Button variant="hero" className="w-full" disabled={loading}>
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isLogin ? (
                language === 'ar' ? 'تسجيل الدخول' : 'Sign In'
              ) : (
                language === 'ar' ? 'إنشاء حساب' : 'Sign Up'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              {isLogin
                ? (language === 'ar' ? 'ما عندك حساب؟ سجل الآن' : "Don't have an account? Sign up")
                : (language === 'ar' ? 'عندك حساب؟ سجل دخول' : 'Already have an account? Sign in')
              }
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
