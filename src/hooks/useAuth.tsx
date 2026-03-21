import { useState, useEffect, useRef } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [useMockAuth, setUseMockAuth] = useState(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
const initializeAuth = async () => {
      try {
        // تحقق من Supabase أولاً
        if (!supabase || !supabase.auth) {
          console.warn('Supabase not configured, using mock auth');
          setUseMockAuth(true);
          loadMockAuth();
          return;
        }

        // اجلب الجلسة الحالية
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        
        if (isMountedRef.current) {
          if (currentSession) {
            setSession(currentSession);
            setUser(currentSession.user);
          } else {
            // لا توجد جلسة Supabase، حاول mock auth
            loadMockAuth();
          }
          setLoading(false);
        }

        // اسمع لتغييرات المصادقة
        if (supabase.auth && supabase.auth.onAuthStateChange) {
          const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (event, supabaseSession) => {
              if (isMountedRef.current) {
                setSession(supabaseSession);
                setUser(supabaseSession?.user ?? null);
              }
            }
          );

          return () => subscription?.unsubscribe();
        }
      } catch (error) {
        console.warn('Auth initialization error, using mock auth:', error);
        if (isMountedRef.current) {
          setUseMockAuth(true);
          loadMockAuth();
        }
      }
    };

    initializeAuth();
  }, []);

  const loadMockAuth = () => {
    try {
      const stored = localStorage.getItem('fitcoach_mock_user');
      if (stored && isMountedRef.current) {
        const mockUser = JSON.parse(stored);
        setUser(mockUser as any);
      }
    } catch (error) {
      console.warn('Mock auth load error:', error);
      localStorage.removeItem('fitcoach_mock_user');
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const signOut = async () => {
    try {
      if (useMockAuth) {
        setUser(null);
        localStorage.removeItem('fitcoach_mock_user');
      } else {
        await supabase.auth.signOut();
        setUser(null);
        setSession(null);
      }
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return { user, session, loading, signOut };
}
