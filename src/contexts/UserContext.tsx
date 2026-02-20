import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';

export interface UserProfile {
  name: string;
  age: number;
  gender: 'male' | 'female';
  weight: number;
  height: number;
  goal: 'bulking' | 'cutting' | 'fitness';
  location: 'home' | 'gym';
  chronicConditions: string;
  onboardingCompleted: boolean;
}

interface UserContextType {
  profile: UserProfile | null;
  setProfile: (profile: UserProfile) => void;
  updateProfile: (updates: Partial<UserProfile>) => void;
  isOnboarded: boolean;
}

const defaultProfile: UserProfile = {
  name: '',
  age: 25,
  gender: 'male',
  weight: 70,
  height: 175,
  goal: 'fitness',
  location: 'home',
  chronicConditions: '',
  onboardingCompleted: false,
};

const UserContext = createContext<UserContextType | undefined>(undefined);
const LEGACY_PROFILE_STORAGE_KEY = 'fitcoach_profile';
const getProfileStorageKey = (userId: string) => `fitcoach_profile_${userId}`;

export function UserProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [profile, setProfileState] = useState<UserProfile | null>(null);

  useEffect(() => {
    localStorage.removeItem(LEGACY_PROFILE_STORAGE_KEY);
  }, []);

  useEffect(() => {
    let isMounted = true;

    if (!user) {
      setProfileState(null);
      return () => {
        isMounted = false;
      };
    }

    const storageKey = getProfileStorageKey(user.id);
    const saved = localStorage.getItem(storageKey);

    if (saved) {
      try {
        if (isMounted) {
          setProfileState(JSON.parse(saved) as UserProfile);
        }
      } catch {
        if (isMounted) {
          setProfileState(null);
        }
      }
    } else {
      setProfileState(null);
    }

    supabase
      .from('profiles')
      .select('*')
      .eq('user_id', user.id)
      .maybeSingle()
      .then(({ data }) => {
        if (!isMounted || !data) return;

        setProfileState({
          ...defaultProfile,
          name: data.name || '',
          age: Number(data.age ?? defaultProfile.age),
          gender: (data.gender as 'male' | 'female') || defaultProfile.gender,
          weight: Number(data.weight ?? defaultProfile.weight),
          height: Number(data.height ?? defaultProfile.height),
          goal: (data.goal as 'bulking' | 'cutting' | 'fitness') || defaultProfile.goal,
          location: (data.location as 'home' | 'gym') || defaultProfile.location,
          chronicConditions: (data as { chronic_conditions?: string }).chronic_conditions || '',
          onboardingCompleted: Boolean(data.onboarding_completed),
        });
      });

    return () => {
      isMounted = false;
    };
  }, [user?.id]);

  useEffect(() => {
    if (!user) return;

    const storageKey = getProfileStorageKey(user.id);
    if (profile) {
      localStorage.setItem(storageKey, JSON.stringify(profile));
    } else {
      localStorage.removeItem(storageKey);
    }
  }, [profile, user?.id]);

  const setProfile = (newProfile: UserProfile) => {
    setProfileState(newProfile);
  };

  const updateProfile = (updates: Partial<UserProfile>) => {
    setProfileState((prev) => ({ ...(prev ?? defaultProfile), ...updates }));
  };

  const isOnboarded = profile?.onboardingCompleted ?? false;

  return (
    <UserContext.Provider value={{ profile, setProfile, updateProfile, isOnboarded }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}

export { defaultProfile };
