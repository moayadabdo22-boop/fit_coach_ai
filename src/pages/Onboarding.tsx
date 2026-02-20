import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, User, Ruler, Target, MapPin, HeartPulse } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser, defaultProfile, UserProfile } from '@/contexts/UserContext';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';
import { useNavigate } from 'react-router-dom';

const steps = ['basic', 'body', 'health', 'goals', 'location'] as const;

export function OnboardingPage() {
  const { t, language, dir } = useLanguage();
  const { setProfile } = useUser();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Partial<UserProfile>>({ ...defaultProfile });

  const updateField = <K extends keyof UserProfile>(field: K, value: UserProfile[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const nextStep = async () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      const finalProfile = { ...defaultProfile, ...formData, onboardingCompleted: true } as UserProfile;
      setProfile(finalProfile);

      if (user) {
        await supabase.from('profiles').upsert({
          user_id: user.id,
          name: finalProfile.name,
          age: finalProfile.age,
          gender: finalProfile.gender,
          weight: finalProfile.weight,
          height: finalProfile.height,
          goal: finalProfile.goal,
          location: finalProfile.location,
          chronic_conditions: finalProfile.chronicConditions || '',
          onboarding_completed: true,
        }, { onConflict: 'user_id' });
      }

      navigate('/workouts');
    }
  };

  const prevStep = () => {
    if (currentStep > 0) setCurrentStep((prev) => prev - 1);
  };

  const stepIcons = [User, Ruler, HeartPulse, Target, MapPin];
  const Icon = stepIcons[currentStep];

  const commonConditions = language === 'ar'
    ? ['سكري', 'ضغط الدم', 'قلب', 'ربو', 'مفاصل', 'ظهر']
    : ['Diabetes', 'Blood Pressure', 'Heart', 'Asthma', 'Joints', 'Back Pain'];

  const toggleCondition = (condition: string) => {
    const current = formData.chronicConditions || '';
    const conditions = current.split(',').map(c => c.trim()).filter(Boolean);
    if (conditions.includes(condition)) {
      updateField('chronicConditions', conditions.filter(c => c !== condition).join(', '));
    } else {
      updateField('chronicConditions', [...conditions, condition].join(', '));
    }
  };

  const hasCondition = (condition: string) => {
    return (formData.chronicConditions || '').split(',').map(c => c.trim()).includes(condition);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-lg">
        <div className="flex gap-2 mb-8">
          {steps.map((_, index) => (
            <div key={index} className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${index <= currentStep ? 'bg-primary shadow-glow' : 'bg-secondary'}`} />
          ))}
        </div>

        <div className="glass-card rounded-2xl p-8">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 rounded-full bg-gradient-primary flex items-center justify-center shadow-glow">
              <Icon className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>

          <h2 className="text-2xl font-bold text-center mb-2">
            {currentStep === 2
              ? (language === 'ar' ? 'الحالة الصحية' : 'Health Status')
              : t(`onboarding.step${currentStep >= 3 ? currentStep : currentStep + 1}`)}
          </h2>
          <p className="text-muted-foreground text-center mb-8">{t('onboarding.welcome')}</p>

          <AnimatePresence mode="wait">
            <motion.div key={currentStep} initial={{ opacity: 0, x: dir === 'rtl' ? -20 : 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: dir === 'rtl' ? 20 : -20 }} transition={{ duration: 0.2 }} className="space-y-6">
              {currentStep === 0 && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">{t('onboarding.name')}</label>
                    <Input value={formData.name || ''} onChange={(e) => updateField('name', e.target.value)} placeholder={language === 'ar' ? 'محمد' : 'John Doe'} className="bg-secondary border-border" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">{t('onboarding.age')}</label>
                    <Input type="number" value={formData.age || ''} onChange={(e) => updateField('age', parseInt(e.target.value) || 0)} placeholder="25" className="bg-secondary border-border" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-3">{t('onboarding.gender')}</label>
                    <div className="grid grid-cols-2 gap-3">
                      {(['male', 'female'] as const).map((gender) => (
                        <button key={gender} onClick={() => updateField('gender', gender)}
                          className={`p-4 rounded-xl border-2 transition-all ${formData.gender === gender ? 'border-primary bg-primary/10' : 'border-border bg-secondary hover:border-primary/50'}`}
                        >
                          <span className="font-medium">{t(`onboarding.${gender}`)}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
              {currentStep === 1 && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">{t('onboarding.weight')}</label>
                    <Input type="number" value={formData.weight || ''} onChange={(e) => updateField('weight', parseInt(e.target.value) || 0)} placeholder="70" className="bg-secondary border-border" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">{t('onboarding.height')}</label>
                    <Input type="number" value={formData.height || ''} onChange={(e) => updateField('height', parseInt(e.target.value) || 0)} placeholder="175" className="bg-secondary border-border" />
                  </div>
                </>
              )}
              {currentStep === 2 && (
                <div>
                  <label className="block text-sm font-medium mb-3">
                    {language === 'ar' ? 'هل تعاني من أمراض مزمنة؟' : 'Do you have any chronic conditions?'}
                  </label>
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    {commonConditions.map((condition) => (
                      <button key={condition} onClick={() => toggleCondition(condition)}
                        className={`p-3 rounded-xl border-2 text-sm transition-all ${hasCondition(condition) ? 'border-primary bg-primary/10 text-primary' : 'border-border bg-secondary hover:border-primary/50'}`}
                      >
                        {condition}
                      </button>
                    ))}
                  </div>
                  <Textarea
                    value={formData.chronicConditions || ''}
                    onChange={(e) => updateField('chronicConditions', e.target.value)}
                    placeholder={language === 'ar' ? 'اكتب أي أمراض أو حالات صحية أخرى...' : 'Type any other conditions...'}
                    className="bg-secondary border-border"
                    rows={3}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    {language === 'ar' ? 'اتركها فاضية اذا ما عندك أي مشاكل صحية' : 'Leave empty if you have no health issues'}
                  </p>
                </div>
              )}
              {currentStep === 3 && (
                <div>
                  <label className="block text-sm font-medium mb-3">{t('onboarding.goal')}</label>
                  <div className="space-y-3">
                    {(['bulking', 'cutting', 'fitness'] as const).map((goal) => (
                      <button key={goal} onClick={() => updateField('goal', goal)}
                        className={`w-full p-4 rounded-xl border-2 text-left transition-all ${formData.goal === goal ? 'border-primary bg-primary/10' : 'border-border bg-secondary hover:border-primary/50'}`}
                      >
                        <span className="font-medium">{t(`onboarding.${goal}`)}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {currentStep === 4 && (
                <div>
                  <label className="block text-sm font-medium mb-3">{t('onboarding.location')}</label>
                  <div className="grid grid-cols-2 gap-3">
                    {(['home', 'gym'] as const).map((loc) => (
                      <button key={loc} onClick={() => updateField('location', loc)}
                        className={`p-6 rounded-xl border-2 transition-all ${formData.location === loc ? 'border-primary bg-primary/10' : 'border-border bg-secondary hover:border-primary/50'}`}
                      >
                        <span className="font-medium text-lg">{t(`onboarding.${loc}`)}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          <div className="flex gap-3 mt-8">
            {currentStep > 0 && (
              <Button variant="outline" onClick={prevStep} className="flex-1">
                {dir === 'rtl' ? <ChevronRight className="w-4 h-4 mr-2" /> : <ChevronLeft className="w-4 h-4 mr-2" />}
                {t('onboarding.back')}
              </Button>
            )}
            <Button variant="hero" onClick={nextStep} className="flex-1">
              {currentStep === steps.length - 1 ? t('onboarding.finish') : t('onboarding.next')}
              {dir === 'rtl' ? <ChevronLeft className="w-4 h-4 ml-2" /> : <ChevronRight className="w-4 h-4 ml-2" />}
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}