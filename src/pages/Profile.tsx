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
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<Partial<typeof profile>>(profile || {});

  useEffect(() => {
    setEditData(profile || {});
  }, [profile]);

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
              fitnessLevel: (data as any).fitness_level || 'beginner',
              trainingDaysPerWeek: Number((data as any).training_days_per_week ?? 3),
              equipment: (data as any).equipment || '',
              injuries: (data as any).injuries || '',
              activityLevel: (data as any).activity_level || 'moderate',
              dietaryPreferences: (data as any).dietary_preferences || '',
              chronicConditions: (data as any).chronic_conditions || '',
              allergies: (data as any).allergies || '',
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

        {(profile.chronicConditions || profile.allergies || profile.dietaryPreferences) && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
            className="glass-card rounded-2xl p-6 mb-6"
          >
            <h2 className="text-lg font-semibold mb-4">{language === 'ar' ? 'معلومات صحية' : 'Health Information'}</h2>
            <div className="space-y-4">
              {profile.chronicConditions && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {language === 'ar' ? 'الأمراض المزمنة' : 'Chronic Conditions'}
                  </p>
                  <p className="text-base text-foreground">{profile.chronicConditions}</p>
                </div>
              )}
              {profile.allergies && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {language === 'ar' ? 'الحساسيات' : 'Allergies'}
                  </p>
                  <p className="text-base text-foreground">{profile.allergies}</p>
                </div>
              )}
              {profile.dietaryPreferences && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {language === 'ar' ? 'التفضيلات الغذائية' : 'Dietary Preferences'}
                  </p>
                  <p className="text-base text-foreground">{profile.dietaryPreferences}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {(profile.fitnessLevel || profile.trainingDaysPerWeek || profile.equipment || profile.injuries || profile.activityLevel) && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.28 }}
            className="glass-card rounded-2xl p-6 mb-6"
          >
            <h2 className="text-lg font-semibold mb-4">{language === 'ar' ? 'تفاصيل التدريب' : 'Training Details'}</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  {language === 'ar' ? 'المستوى' : 'Level'}
                </p>
                <p className="text-base text-foreground">{t(`onboarding.${profile.fitnessLevel}`)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  {language === 'ar' ? 'أيام التمرين بالأسبوع' : 'Training Days / Week'}
                </p>
                <p className="text-base text-foreground">{profile.trainingDaysPerWeek}</p>
              </div>
              {profile.activityLevel && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">
                    {language === 'ar' ? 'مستوى النشاط' : 'Activity Level'}
                  </p>
                  <p className="text-base text-foreground">{t(`onboarding.activity.${profile.activityLevel}`)}</p>
                </div>
              )}
              {profile.equipment && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">
                    {language === 'ar' ? 'المعدات' : 'Equipment'}
                  </p>
                  <p className="text-base text-foreground">{profile.equipment}</p>
                </div>
              )}
              {profile.injuries && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">
                    {language === 'ar' ? 'إصابات' : 'Injuries'}
                  </p>
                  <p className="text-base text-foreground">{profile.injuries}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="space-y-3">
          <Button variant="outline" className="w-full" onClick={() => setIsEditing(!isEditing)}>
            <Edit className="w-4 h-4 mr-2" />
            {isEditing ? (language === 'ar' ? 'إلغاء' : 'Cancel') : (language === 'ar' ? 'تعديل البيانات' : 'Edit Data')}
          </Button>
          
          {isEditing && (
            <div className="glass-card rounded-2xl p-6 space-y-4 mb-4">
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'المستوى' : 'Fitness Level'}</label>
                <select
                  value={editData.fitnessLevel || 'beginner'}
                  onChange={(e) => setEditData({ ...editData, fitnessLevel: e.target.value as any })}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                >
                  <option value="beginner">{t('onboarding.beginner')}</option>
                  <option value="intermediate">{t('onboarding.intermediate')}</option>
                  <option value="advanced">{t('onboarding.advanced')}</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'أيام التمرين بالأسبوع' : 'Training Days / Week'}</label>
                <input
                  type="number"
                  min={1}
                  max={7}
                  value={editData.trainingDaysPerWeek || 3}
                  onChange={(e) => setEditData({ ...editData, trainingDaysPerWeek: parseInt(e.target.value) || 0 })}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'مستوى النشاط' : 'Activity Level'}</label>
                <select
                  value={editData.activityLevel || 'moderate'}
                  onChange={(e) => setEditData({ ...editData, activityLevel: e.target.value as any })}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                >
                  <option value="low">{t('onboarding.activity.low')}</option>
                  <option value="moderate">{t('onboarding.activity.moderate')}</option>
                  <option value="high">{t('onboarding.activity.high')}</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'المعدات' : 'Equipment'}</label>
                <input
                  type="text"
                  value={editData.equipment || ''}
                  onChange={(e) => setEditData({ ...editData, equipment: e.target.value })}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                  placeholder={language === 'ar' ? 'مثال: دمبل، بار...' : 'e.g. dumbbells, barbell...'}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'إصابات' : 'Injuries'}</label>
                <input
                  type="text"
                  value={editData.injuries || ''}
                  onChange={(e) => setEditData({ ...editData, injuries: e.target.value })}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                  placeholder={language === 'ar' ? 'اكتب أي إصابة...' : 'List any injuries...'}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'الأمراض المزمنة' : 'Chronic Conditions'}</label>
                <input
                  type="text"
                  value={editData.chronicConditions || ''}
                  onChange={(e) => setEditData({...editData, chronicConditions: e.target.value})}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                  placeholder={language === 'ar' ? 'أدخل الأمراض المزمنة' : 'Enter chronic conditions'}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'الحساسيات' : 'Allergies'}</label>
                <input
                  type="text"
                  value={editData.allergies || ''}
                  onChange={(e) => setEditData({...editData, allergies: e.target.value})}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                  placeholder={language === 'ar' ? 'أدخل الحساسيات' : 'Enter allergies'}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">{language === 'ar' ? 'التفضيلات الغذائية' : 'Dietary Preferences'}</label>
                <input
                  type="text"
                  value={editData.dietaryPreferences || ''}
                  onChange={(e) => setEditData({...editData, dietaryPreferences: e.target.value})}
                  className="w-full mt-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border text-foreground"
                  placeholder={language === 'ar' ? 'أدخل التفضيلات الغذائية' : 'Enter dietary preferences'}
                />
              </div>
              <Button
                variant="hero"
                className="w-full"
                onClick={async () => {
                  updateProfile(editData as any);
                  setIsEditing(false);
                  if (user && supabase && supabase.from) {
                    try {
                      await supabase
                        .from('profiles')
                        .update({
                          fitness_level: editData.fitnessLevel || null,
                          training_days_per_week: editData.trainingDaysPerWeek || null,
                          equipment: editData.equipment || null,
                          injuries: editData.injuries || null,
                          activity_level: editData.activityLevel || null,
                          dietary_preferences: editData.dietaryPreferences || null,
                          chronic_conditions: editData.chronicConditions || null,
                          allergies: editData.allergies || null,
                          updated_at: new Date().toISOString(),
                        })
                        .eq('user_id', user.id);
                    } catch (error) {
                      console.warn('Failed updating profile in Supabase:', error);
                    }
                  }
                }}
              >
                {language === 'ar' ? 'حفظ التغييرات' : 'Save Changes'}
              </Button>
            </div>
          )}
          
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
