import React, { createContext, useContext, useState, ReactNode } from 'react';
import { repairMojibake } from '@/lib/text';

type Language = 'en' | 'ar';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  dir: 'ltr' | 'rtl';
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navigation
    'nav.home': 'Home',
    'nav.workouts': 'Workouts',
    'nav.coach': 'AI Coach',
    'nav.profile': 'Profile',
    'nav.schedule': 'Schedule',

    // Hero
    'hero.title': 'TRANSFORM YOUR BODY',
    'hero.subtitle': 'Personalized workouts powered by AI. Get custom training plans, nutrition advice, and real-time coaching.',
    'hero.cta': 'Start Your Journey',
    'hero.secondary': 'Explore Workouts',

    // Onboarding
    'onboarding.welcome': "Let's Get Started",
    'onboarding.step1': 'Basic Info',
    'onboarding.step2': 'Body Stats',
    'onboarding.step3': 'Your Goals',
    'onboarding.step4': 'Training Details',
    'onboarding.step5': 'Workout Preference',
    'onboarding.name': "What's your name?",
    'onboarding.age': 'How old are you?',
    'onboarding.gender': 'Gender',
    'onboarding.male': 'Male',
    'onboarding.female': 'Female',
    'onboarding.weight': 'Weight (kg)',
    'onboarding.height': 'Height (cm)',
    'onboarding.goal': "What's your goal?",
    'onboarding.bulking': 'Build Muscle',
    'onboarding.cutting': 'Lose Weight',
    'onboarding.fitness': 'General Fitness',
    'onboarding.beginner': 'Beginner',
    'onboarding.intermediate': 'Intermediate',
    'onboarding.advanced': 'Advanced',
    'onboarding.activity.low': 'Low',
    'onboarding.activity.moderate': 'Moderate',
    'onboarding.activity.high': 'High',
    'onboarding.location': 'Where do you workout?',
    'onboarding.home': 'Home',
    'onboarding.gym': 'Gym',
    'onboarding.next': 'Continue',
    'onboarding.back': 'Back',
    'onboarding.finish': 'Start Training',

    // Workouts
    'workouts.title': 'MUSCLE MAP',
    'workouts.subtitle': 'Select target muscles to find exercises',
    'workouts.filter.all': 'All',
    'workouts.filter.goal': 'By Goal',
    'workouts.filter.muscle': 'By Muscle',
    'workouts.exercises': 'exercises found',
    'workouts.sets': 'Sets',
    'workouts.reps': 'Reps',
    'workouts.watch': 'Watch Video',
    'workouts.noResults': 'No exercises found. Try adjusting your filters.',

    // Muscles
    'muscle.chest': 'Chest',
    'muscle.back': 'Back',
    'muscle.shoulders': 'Shoulders',
    'muscle.biceps': 'Biceps',
    'muscle.triceps': 'Triceps',
    'muscle.abs': 'Abs',
    'muscle.quads': 'Quads',
    'muscle.hamstrings': 'Hamstrings',
    'muscle.glutes': 'Glutes',
    'muscle.calves': 'Calves',

    // AI Coach
    'coach.title': 'AI Fitness Coach',
    'coach.subtitle': 'Your personal fitness & nutrition advisor',
    'coach.placeholder': 'Ask me anything about fitness...',
    'coach.send': 'Send',
    'coach.greeting': "Hey! 👋 I'm your personal AI fitness coach. Ask me about workouts, nutrition, or anything fitness-related! You can also use voice to chat. What can I help you with today?",
    'coach.newChat': 'New Chat',
    'coach.history': 'Chat History',
    'coach.autoSpeakOn': 'Auto-speak is on',
    'coach.autoSpeakOff': 'Auto-speak is off',

    // Common
    'common.loading': 'Loading...',
    'common.error': 'Something went wrong',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
  },
  ar: {
    // Navigation
    'nav.home': 'الرئيسية',
    'nav.workouts': 'التمارين',
    'nav.coach': 'المدرب الذكي',
    'nav.profile': 'الملف',
    'nav.schedule': 'الجدول',

    // Hero
    'hero.title': 'غيّر جسمك',
    'hero.subtitle': 'تمارين مخصصة بالذكاء الاصطناعي. احصل على خطط تدريب شخصية ونصائح غذائية وتدريب مباشر.',
    'hero.cta': 'ابدأ رحلتك',
    'hero.secondary': 'استكشف التمارين',

    // Onboarding
    'onboarding.welcome': 'هيا نبدأ',
    'onboarding.step1': 'معلومات أساسية',
    'onboarding.step2': 'قياسات الجسم',
    'onboarding.step3': 'أهدافك',
    'onboarding.step4': 'تفاصيل التدريب',
    'onboarding.step5': 'مكان التمرين',
    'onboarding.name': 'شو اسمك؟',
    'onboarding.age': 'كم عمرك؟',
    'onboarding.gender': 'الجنس',
    'onboarding.male': 'ذكر',
    'onboarding.female': 'أنثى',
    'onboarding.weight': 'الوزن (كغ)',
    'onboarding.height': 'الطول (سم)',
    'onboarding.goal': 'شو هدفك؟',
    'onboarding.bulking': 'بناء عضلات',
    'onboarding.cutting': 'إنقاص الوزن',
    'onboarding.fitness': 'لياقة عامة',
    'onboarding.beginner': 'مبتدئ',
    'onboarding.intermediate': 'متوسط',
    'onboarding.advanced': 'متقدم',
    'onboarding.activity.low': 'منخفض',
    'onboarding.activity.moderate': 'متوسط',
    'onboarding.activity.high': 'مرتفع',
    'onboarding.location': 'وين بتتمرن؟',
    'onboarding.home': 'البيت',
    'onboarding.gym': 'الجيم',
    'onboarding.next': 'التالي',
    'onboarding.back': 'رجوع',
    'onboarding.finish': 'ابدأ التمرين',

    // Workouts
    'workouts.title': 'خريطة العضلات',
    'workouts.subtitle': 'اختر العضلات المستهدفة لعرض التمارين',
    'workouts.filter.all': 'الكل',
    'workouts.filter.goal': 'حسب الهدف',
    'workouts.filter.muscle': 'حسب العضلة',
    'workouts.exercises': 'تمرين',
    'workouts.sets': 'مجموعات',
    'workouts.reps': 'تكرارات',
    'workouts.watch': 'شاهد الفيديو',
    'workouts.noResults': 'ما لقيت تمارين. جرب تغير الفلاتر.',

    // Muscles
    'muscle.chest': 'الصدر',
    'muscle.back': 'الظهر',
    'muscle.shoulders': 'الأكتاف',
    'muscle.biceps': 'الباي',
    'muscle.triceps': 'التراي',
    'muscle.abs': 'البطن',
    'muscle.quads': 'الفخذ الأمامي',
    'muscle.hamstrings': 'الفخذ الخلفي',
    'muscle.glutes': 'المؤخرة',
    'muscle.calves': 'السمانة',

    // AI Coach
    'coach.title': 'المدرب الذكي',
    'coach.subtitle': 'مستشارك الشخصي للتمارين والتغذية',
    'coach.placeholder': 'اسألني أي شي عن اللياقة...',
    'coach.send': 'إرسال',
    'coach.greeting': 'مرحبا! 👋 أنا مدربك الشخصي بالذكاء الاصطناعي. اسألني عن التمارين أو التغذية أو أي شي يخص اللياقة! بتقدر كمان تحكيلي صوت. كيف بقدر أساعدك اليوم؟',
    'coach.newChat': 'محادثة جديدة',
    'coach.history': 'سجل المحادثات',
    'coach.autoSpeakOn': 'القراءة التلقائية مفعلة',
    'coach.autoSpeakOff': 'القراءة التلقائية متوقفة',

    // Common
    'common.loading': 'جاري التحميل...',
    'common.error': 'صار خطأ',
    'common.save': 'حفظ',
    'common.cancel': 'إلغاء',
  },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('en');

  const t = (key: string): string => {
    const value = translations[language][key] || key;
    return repairMojibake(value);
  };

  const dir = language === 'ar' ? 'rtl' : 'ltr';

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, dir }}>
      <div dir={dir}>{children}</div>
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
