import { useState, useEffect, useRef } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '@/integrations/supabase/client';

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

  // Listen to storage changes for mock auth updates
  useEffect(() => {
    if (!useMockAuth) return;

    let isMountedLocal = true;
    let pollInterval: NodeJS.Timeout | null = null;

    const handleStorageChange = () => {
      if (isMountedLocal) {
        loadMockAuth();
      }
    };

    // Check localStorage immediately
    loadMockAuth();

    // Listen to storage events from other tabs/windows
    window.addEventListener('storage', handleStorageChange);

    // Poll localStorage to catch same-tab changes more frequently
    pollInterval = setInterval(() => {
      if (isMountedLocal && !user) {
        const stored = localStorage.getItem('fitcoach_mock_user');
        if (stored) {
          loadMockAuth();
        }
      }
    }, 50); // Check every 50ms

    return () => {
      isMountedLocal = false;
      window.removeEventListener('storage', handleStorageChange);
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [useMockAuth]);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const supabaseReady = isSupabaseConfigured();

        if (supabaseReady && supabase?.auth) {
          try {
            localStorage.removeItem('fitcoach_mock_user');
          } catch {
            // ignore storage cleanup failures
          }

          const sessionResult = await supabase.auth.getSession();
          const currentSession = sessionResult?.data?.session;

          if (currentSession && isMountedRef.current) {
            setSession(currentSession);
            setUser(currentSession.user);
            setUseMockAuth(false);
          }

          if (supabase.auth.onAuthStateChange) {
            const { data: { subscription } } = supabase.auth.onAuthStateChange(
              (_event, supabaseSession) => {
                if (isMountedRef.current) {
                  setSession(supabaseSession);
                  setUser(supabaseSession?.user ?? null);
                  setUseMockAuth(false);
                }
              }
            );

            if (isMountedRef.current) {
              setLoading(false);
            }
            return () => subscription?.unsubscribe();
          }

          if (isMountedRef.current) {
            setLoading(false);
          }
          return;
        }

        // Supabase not configured -> allow mock auth
        setUseMockAuth(true);
        loadMockAuth();
      } catch (error) {
        console.warn('Auth initialization error:', error);
        if (!isSupabaseConfigured() && isMountedRef.current) {
          setUseMockAuth(true);
          setLoading(false);
        }
      }
    };

    initializeAuth();
  }, []);

  const loadMockAuth = () => {
    const memoryUser = (globalThis as any).__fitcoach_mock_user;
    try {
      const stored = localStorage.getItem('fitcoach_mock_user');
      if (stored && isMountedRef.current) {
        const mockUser = JSON.parse(stored);
        setUser(mockUser as any);
        setUseMockAuth(true);
        setLoading(false);
        return;
      }
      if (memoryUser && isMountedRef.current) {
        setUser(memoryUser as any);
        setUseMockAuth(true);
        setLoading(false);
        return;
      }
      // لا توجد بيانات في localStorage، تخطي المصادقة
      if (isMountedRef.current) {
        setLoading(false);
      }
    } catch (error) {
      console.warn('Mock auth load error:', error);
      localStorage.removeItem('fitcoach_mock_user');
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
      // Force logout on error
      setUser(null);
      localStorage.removeItem('fitcoach_mock_user');
    }
  };

  return { user, session, loading, signOut };
}
