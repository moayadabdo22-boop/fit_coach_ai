import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dumbbell, Mail, Lock, User, Eye, EyeOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useLanguage } from '@/contexts/LanguageContext';
import { supabase } from '@/integrations/supabase/client';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';

export function AuthPage() {
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) {
        navigate('/', { replace: true });
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        navigate('/', { replace: true });
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          if (error.message.includes('Invalid login credentials')) {
            toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: language === 'ar' ? 'البريد الإلكتروني أو كلمة المرور غير صحيحة' : 'Invalid email or password' });
          } else if (error.message.includes('Email not confirmed')) {
            toast({ variant: 'destructive', title: language === 'ar' ? 'تنبيه' : 'Notice', description: language === 'ar' ? 'يرجى تأكيد بريدك الإلكتروني أولاً' : 'Please confirm your email first' });
          } else {
            toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: error.message });
          }
        }
      } else {
        if (password.length < 6) {
          toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: language === 'ar' ? 'كلمة المرور يجب أن تكون 6 أحرف على الأقل' : 'Password must be at least 6 characters' });
          setLoading(false);
          return;
        }
        const redirectUrl = `${window.location.origin}/`;
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: redirectUrl,
            data: { name },
          },
        });
        if (error) {
          if (error.message.includes('already registered')) {
            toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: language === 'ar' ? 'هذا البريد مسجل مسبقاً، جرب تسجيل الدخول' : 'This email is already registered. Try logging in.' });
          } else {
            toast({ variant: 'destructive', title: language === 'ar' ? 'خطأ' : 'Error', description: error.message });
          }
        } else {
          toast({
            title: language === 'ar' ? 'تم التسجيل!' : 'Account created!',
            description: language === 'ar' ? 'تحقق من بريدك الإلكتروني لتأكيد الحساب' : 'Check your email to confirm your account',
          });
        }
      }
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: 'Something went wrong' });
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
