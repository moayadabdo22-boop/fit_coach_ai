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
  fitnessLevel: 'beginner' | 'intermediate' | 'advanced';
  trainingDaysPerWeek: number;
  equipment: string;
  injuries: string;
  activityLevel: 'low' | 'moderate' | 'high';
  dietaryPreferences: string;
  chronicConditions: string;
  allergies: string;
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
  fitnessLevel: 'beginner',
  trainingDaysPerWeek: 3,
  equipment: '',
  injuries: '',
  activityLevel: 'moderate',
  dietaryPreferences: '',
  chronicConditions: '',
  allergies: '',
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

    // فقط حاول Supabase إذا كانت مكونة
    if (!supabase || !supabase.from) {
      console.warn('Supabase not available, skipping profile fetch');
      return () => {
        isMounted = false;
      };
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
          fitnessLevel: (data.fitness_level as 'beginner' | 'intermediate' | 'advanced') || defaultProfile.fitnessLevel,
          trainingDaysPerWeek: Number((data as { training_days_per_week?: number }).training_days_per_week ?? defaultProfile.trainingDaysPerWeek),
          equipment: (data as { equipment?: string }).equipment || '',
          injuries: (data as { injuries?: string }).injuries || '',
          activityLevel: (data as { activity_level?: string }).activity_level as 'low' | 'moderate' | 'high' || defaultProfile.activityLevel,
          dietaryPreferences: (data as { dietary_preferences?: string }).dietary_preferences || '',
          chronicConditions: (data as { chronic_conditions?: string }).chronic_conditions || '',
          allergies: (data as { allergies?: string }).allergies || '',
          onboardingCompleted: Boolean(data.onboarding_completed),
        });
      })
      .catch(() => {
        // تجاهل الأخطاء من Supabase
        console.debug('Could not fetch profile from Supabase');
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

export function useUser(): UserContextType {
  const context = useContext(UserContext);
  if (!context) {
    // إذا لم يكن هناك context، عيد قيماً افتراضية
    return {
      profile: null,
      setProfile: () => {},
      updateProfile: () => {},
      isOnboarded: false,
    };
  }
  return context;
}

export { defaultProfile };
