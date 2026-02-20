import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { User, Ruler, Weight, Target, MapPin, Edit, LogOut, Calendar } from 'lucide-react';
import { Navbar } from '@/components/layout/Navbar';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';

export function ProfilePage() {
  const { t, language } = useLanguage();
  const { profile, updateProfile } = useUser();
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  // Sync profile from DB on mount
  useEffect(() => {
    if (user) {
      supabase
        .from('profiles')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle()
        .then(({ data }) => {
          if (data && data.onboarding_completed) {
            updateProfile({
              name: data.name,
              age: data.age,
              gender: data.gender as 'male' | 'female',
              weight: Number(data.weight),
              height: Number(data.height),
              goal: data.goal as 'bulking' | 'cutting' | 'fitness',
              location: data.location as 'home' | 'gym',
              chronicConditions: (data as any).chronic_conditions || '',
              onboardingCompleted: data.onboarding_completed,
            });
          }
        });
    }
  }, [user]);

  if (!profile || !profile.onboardingCompleted) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Button variant="hero" onClick={() => navigate('/onboarding')}>
              {language === 'ar' ? 'أكمل ملفك الشخصي' : 'Complete Your Profile'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const stats = [
    { icon: User, label: t('onboarding.age'), value: `${profile.age} ${language === 'ar' ? 'سنة' : 'years'}` },
    { icon: Ruler, label: t('onboarding.height'), value: `${profile.height} cm` },
    { icon: Weight, label: t('onboarding.weight'), value: `${profile.weight} kg` },
    { icon: Target, label: language === 'ar' ? 'الهدف' : 'Goal', value: t(`onboarding.${profile.goal}`) },
    { icon: MapPin, label: language === 'ar' ? 'المكان' : 'Location', value: t(`onboarding.${profile.location}`) },
  ];

  const bmi = profile.weight / Math.pow(profile.height / 100, 2);
  const bmiCategory = bmi < 18.5 ? (language === 'ar' ? 'نقص وزن' : 'Underweight') : bmi < 25 ? (language === 'ar' ? 'طبيعي' : 'Normal') : bmi < 30 ? (language === 'ar' ? 'زيادة وزن' : 'Overweight') : (language === 'ar' ? 'سمنة' : 'Obese');

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Navbar />
      <main className="container mx-auto px-4 pt-24 max-w-2xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-primary flex items-center justify-center shadow-glow">
            <span className="font-display text-4xl text-primary-foreground">
              {profile.name?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          <h1 className="font-display text-4xl text-foreground mb-1">{profile.name || 'User'}</h1>
          <p className="text-muted-foreground">
            {t(`onboarding.${profile.gender}`)} • {t(`onboarding.${profile.goal}`)}
          </p>
          {user && <p className="text-xs text-muted-foreground mt-1">{user.email}</p>}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-6 mb-6"
        >
          <h2 className="text-lg font-semibold mb-4">{language === 'ar' ? 'مؤشر كتلة الجسم' : 'Body Mass Index'}</h2>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-4xl font-bold gradient-text">{bmi.toFixed(1)}</span>
              <p className="text-muted-foreground mt-1">{bmiCategory}</p>
            </div>
            <div className="w-32 h-3 bg-secondary rounded-full overflow-hidden">
              <div className="h-full bg-gradient-primary rounded-full transition-all" style={{ width: `${Math.min((bmi / 40) * 100, 100)}%` }} />
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass-card rounded-2xl p-6 mb-6"
        >
          <h2 className="text-lg font-semibold mb-4">{language === 'ar' ? 'إحصائياتك' : 'Your Stats'}</h2>
          <div className="grid grid-cols-2 gap-4">
            {stats.map((stat, index) => (
              <div key={index} className="bg-secondary/50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className="w-4 h-4 text-primary" />
                  <span className="text-sm text-muted-foreground">{stat.label}</span>
                </div>
                <p className="text-lg font-semibold">{stat.value}</p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="space-y-3">
          <Button variant="outline" className="w-full" onClick={() => navigate('/onboarding')}>
            <Edit className="w-4 h-4 mr-2" />
            {language === 'ar' ? 'تعديل الملف الشخصي' : 'Edit Profile'}
          </Button>
          <Button variant="outline" className="w-full" onClick={() => navigate('/schedule')}>
            <Calendar className="w-4 h-4 mr-2" />
            {language === 'ar' ? 'جدول التمارين' : 'Workout Schedule'}
          </Button>
          {user && (
            <Button variant="ghost" className="w-full text-destructive hover:text-destructive" onClick={signOut}>
              <LogOut className="w-4 h-4 mr-2" />
              {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
            </Button>
          )}
        </motion.div>
      </main>
    </div>
  );
}
