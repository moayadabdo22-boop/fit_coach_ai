import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Check, ChevronLeft, ChevronRight, Dumbbell, Loader2, Trash2, UtensilsCrossed } from 'lucide-react';
import { Navbar } from '@/components/layout/Navbar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface WorkoutExercise {
  name: string;
  nameAr: string;
  sets: string;
  reps: string;
}

interface NutritionMeal {
  name: string;
  nameAr: string;
  description: string;
  descriptionAr: string;
  calories: string;
}

interface PlanDay {
  day: string;
  dayAr: string;
  exercises?: WorkoutExercise[];
  meals?: NutritionMeal[];
}

interface WorkoutPlan {
  id: string;
  title: string;
  title_ar: string;
  plan_data: PlanDay[];
  is_active: boolean;
  created_at: string;
}

interface Completion {
  id: string;
  plan_id: string;
  day_index: number;
  exercise_index: number;
  log_date: string;
}

interface DailyLog {
  id: string;
  log_date: string;
  workout_notes: string;
  nutrition_notes: string;
  mood: string;
}

const NUTRITION_PREFIXES = ['\u{1F37D}\uFE0F'];
const isNutritionPlanTitle = (title: string) => NUTRITION_PREFIXES.some(prefix => title.startsWith(prefix));

// Map plan day names to JS day numbers (0=Sun, 6=Sat)
const dayNameToIndex: Record<string, number> = {
  'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
  'thursday': 4, 'friday': 5, 'saturday': 6,
  'الأحد': 0, 'الاثنين': 1, 'الثلاثاء': 2, 'الأربعاء': 3,
  'الخميس': 4, 'الجمعة': 5, 'السبت': 6,
};

function getPlanDayIndex(dayStr: string): number {
  const lower = dayStr.toLowerCase().split(' - ')[0].split(' – ')[0].trim();
  return dayNameToIndex[lower] ?? -1;
}

function getWeekDates(weekOffset: number): Date[] {
  const today = new Date();
  const currentDay = today.getDay(); // 0=Sun
  // Start week on Saturday (6)
  const satOffset = (currentDay + 1) % 7;
  const saturday = new Date(today);
  saturday.setDate(today.getDate() - satOffset + (weekOffset * 7));
  saturday.setHours(0, 0, 0, 0);
  
  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(saturday);
    d.setDate(saturday.getDate() + i);
    dates.push(d);
  }
  return dates;
}

function formatLogDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

const dayOrder = [6, 0, 1, 2, 3, 4, 5]; // Sat, Sun, Mon, Tue, Wed, Thu, Fri

export function SchedulePage() {
  const { language } = useLanguage();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [plans, setPlans] = useState<WorkoutPlan[]>([]);
  const [completions, setCompletions] = useState<Completion[]>([]);
  const [dailyLogs, setDailyLogs] = useState<DailyLog[]>([]);
  const [logDraft, setLogDraft] = useState({ workout_notes: '', nutrition_notes: '', mood: '' });
  const [savingLog, setSavingLog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [weekOffset, setWeekOffset] = useState(0);
  const [selectedDateIdx, setSelectedDateIdx] = useState(-1); // index into weekDates
  const [viewTab, setViewTab] = useState<'workout' | 'nutrition'>('workout');

  const weekDates = useMemo(() => getWeekDates(weekOffset), [weekOffset]);

  // Auto-select today
  useEffect(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const idx = weekDates.findIndex(d => d.getTime() === today.getTime());
    setSelectedDateIdx(idx >= 0 ? idx : 0);
  }, [weekDates]);

  const workoutPlans = plans.filter(p => !isNutritionPlanTitle(p.title));
  const nutritionPlans = plans.filter(p => isNutritionPlanTitle(p.title));
  const activePlan = workoutPlans.find(p => p.is_active) || workoutPlans[0] || null;
  const activeNutritionPlan = nutritionPlans.find(p => p.is_active) || nutritionPlans[0] || null;

  useEffect(() => {
    if (user) fetchPlans();
  }, [user]);

  const fetchPlans = async () => {
    if (!user) return;
    setLoading(true);
    
    const { data: plansData } = await supabase
      .from('workout_plans')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
    
    if (plansData) {
      const parsed = plansData.map(p => ({
        ...p,
        plan_data: (p.plan_data as any) as PlanDay[],
      }));
      setPlans(parsed);
      
      // Load completions for all plans
      const { data: compData } = await supabase
        .from('workout_completions')
        .select('id,plan_id,day_index,exercise_index,log_date')
        .eq('user_id', user.id);
      if (compData) setCompletions(compData);
    }
    const { data: logsData } = await supabase
      .from('daily_logs')
      .select('id,log_date,workout_notes,nutrition_notes,mood')
      .eq('user_id', user.id);
    if (logsData) setDailyLogs(logsData);
    setLoading(false);
  };

  const saveDailyLog = async () => {
    if (!user) return;
    setSavingLog(true);
    try {
      const payload = {
        user_id: user.id,
        log_date: selectedLogDate,
        workout_notes: logDraft.workout_notes || '',
        nutrition_notes: logDraft.nutrition_notes || '',
        mood: logDraft.mood || '',
      };
      const { data } = await supabase
        .from('daily_logs')
        .upsert(payload, { onConflict: 'user_id,log_date' })
        .select()
        .single();
      if (data) {
        setDailyLogs(prev => {
          const existing = prev.find(log => log.log_date === selectedLogDate);
          if (existing) {
            return prev.map(log => log.log_date === selectedLogDate ? data : log);
          }
          return [...prev, data];
        });
      }
      toast({
        title: language === 'ar' ? 'تم الحفظ' : 'Saved',
        description: language === 'ar' ? 'تم حفظ ملاحظات اليوم.' : 'Daily log saved.',
      });
    } catch (error) {
      console.error('Failed saving daily log', error);
      toast({
        variant: 'destructive',
        title: language === 'ar' ? 'خطأ' : 'Error',
        description: language === 'ar' ? 'فشل حفظ الملاحظات.' : 'Could not save daily log.',
      });
    } finally {
      setSavingLog(false);
    }
  };

  const hasDailyActivity = (date: Date) => {
    const logDate = formatLogDate(date);
    const hasCompletion = completions.some((c) => c.log_date === logDate);
    const log = dailyLogs.find((l) => l.log_date === logDate);
    const hasNotes = Boolean(log && (log.workout_notes || log.nutrition_notes || log.mood));
    return hasCompletion || hasNotes;
  };

  // Find which plan day matches the selected calendar day
  const getMatchingPlanDay = (plan: WorkoutPlan | null, date: Date): { day: PlanDay; index: number } | null => {
    if (!plan) return null;
    const jsDay = date.getDay(); // 0=Sun...6=Sat
    for (let i = 0; i < plan.plan_data.length; i++) {
      const planDayIdx = getPlanDayIndex(plan.plan_data[i].day) !== -1 
        ? getPlanDayIndex(plan.plan_data[i].day) 
        : getPlanDayIndex(plan.plan_data[i].dayAr || '');
      if (planDayIdx === jsDay) return { day: plan.plan_data[i], index: i };
    }
    return null;
  };

  const currentPlan = viewTab === 'workout' ? activePlan : activeNutritionPlan;
  const selectedDate = weekDates[selectedDateIdx] || weekDates[0];
  const selectedLogDate = useMemo(() => formatLogDate(selectedDate), [selectedDate]);
  const matchingDay = getMatchingPlanDay(currentPlan, selectedDate);
  const planProgress = useMemo(() => {
    if (!currentPlan) return null;
    const totalItems = currentPlan.plan_data.reduce((sum, day) => {
      const exercises = Array.isArray(day.exercises) ? day.exercises.length : 0;
      const meals = Array.isArray(day.meals) ? day.meals.length : 0;
      return sum + exercises + meals;
    }, 0);
    const completedItems = completions.filter((c) => c.plan_id === currentPlan.id).length;
    const percent = totalItems > 0 ? Math.min(100, Math.round((completedItems / totalItems) * 100)) : 0;
    const remaining = totalItems > 0 ? Math.max(0, 100 - percent) : 100;
    return { totalItems, completedItems, percent, remaining };
  }, [currentPlan, completions]);

  const dailyProgress = useMemo(() => {
    if (!matchingDay || !currentPlan) return null;
    const exercises = Array.isArray(matchingDay.day.exercises) ? matchingDay.day.exercises.length : 0;
    const meals = Array.isArray(matchingDay.day.meals) ? matchingDay.day.meals.length : 0;
    const total = exercises + meals;
    if (total === 0) return { total: 0, completed: 0, percent: 0 };

    const completed = completions.filter(
      (c) =>
        c.plan_id === currentPlan.id &&
        c.day_index === matchingDay.index &&
        c.log_date === selectedLogDate
    ).length;
    const percent = Math.min(100, Math.round((completed / total) * 100));
    return { total, completed, percent };
  }, [matchingDay, currentPlan, completions, selectedLogDate]);

  const currentDailyLog = useMemo(() => {
    return dailyLogs.find((log) => log.log_date === selectedLogDate) || null;
  }, [dailyLogs, selectedLogDate]);

  useEffect(() => {
    if (currentDailyLog) {
      setLogDraft({
        workout_notes: currentDailyLog.workout_notes || '',
        nutrition_notes: currentDailyLog.nutrition_notes || '',
        mood: currentDailyLog.mood || '',
      });
    } else {
      setLogDraft({ workout_notes: '', nutrition_notes: '', mood: '' });
    }
  }, [currentDailyLog]);

  const toggleCompletion = async (dayIndex: number, exerciseIndex: number, planId?: string) => {
    if (!user) return;
    const targetPlanId = planId || currentPlan?.id;
    if (!targetPlanId) return;
    
    const existing = completions.find(
      c =>
        c.plan_id === targetPlanId &&
        c.day_index === dayIndex &&
        c.exercise_index === exerciseIndex &&
        c.log_date === selectedLogDate
    );
    
    if (existing) {
      await supabase.from('workout_completions').delete().eq('id', existing.id);
      setCompletions(prev => prev.filter(c => c.id !== existing.id));
    } else {
      const { data } = await supabase.from('workout_completions').insert({
        user_id: user.id,
        plan_id: targetPlanId,
        day_index: dayIndex,
        exercise_index: exerciseIndex,
        log_date: selectedLogDate,
      }).select().single();
      if (data) setCompletions(prev => [...prev, data]);
    }
  };

  const isCompleted = (dayIndex: number, exerciseIndex: number, planId?: string) => {
    const pid = planId || currentPlan?.id;
    return completions.some(
      c =>
        c.plan_id === pid &&
        c.day_index === dayIndex &&
        c.exercise_index === exerciseIndex &&
        c.log_date === selectedLogDate
    );
  };

  const deletePlan = async (planId: string) => {
    await supabase.from('workout_plans').delete().eq('id', planId);
    setPlans(prev => prev.filter(p => p.id !== planId));
    toast({ title: language === 'ar' ? 'تم حذف الخطة' : 'Plan deleted' });
  };

  const activatePlan = async (plan: WorkoutPlan) => {
    if (!user) return;
    const isNutrition = isNutritionPlanTitle(plan.title);
    const sameTypePlanIds = plans
      .filter(p => isNutrition ? isNutritionPlanTitle(p.title) : !isNutritionPlanTitle(p.title))
      .map(p => p.id);

    if (sameTypePlanIds.length > 0) {
      await supabase.from('workout_plans').update({ is_active: false }).in('id', sameTypePlanIds);
    }
    await supabase.from('workout_plans').update({ is_active: true }).eq('id', plan.id);
    setPlans(prev => prev.map(p =>
      (isNutrition ? isNutritionPlanTitle(p.title) : !isNutritionPlanTitle(p.title))
        ? { ...p, is_active: p.id === plan.id }
        : p
    ));

    toast({ title: language === 'ar' ? 'تم تفعيل الخطة' : 'Plan activated!' });
  };

  const formatDateShort = (date: Date) => {
    return date.toLocaleDateString(language === 'ar' ? 'ar' : 'en', { day: 'numeric' });
  };

  const formatDayName = (date: Date) => {
    return date.toLocaleDateString(language === 'ar' ? 'ar' : 'en', { weekday: 'short' });
  };

  const formatWeekRange = () => {
    const start = weekDates[0];
    const end = weekDates[6];
    const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    const locale = language === 'ar' ? 'ar' : 'en';
    return `${start.toLocaleDateString(locale, opts)} - ${end.toLocaleDateString(locale, opts)}, ${end.getFullYear()}`;
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();
  };

  if (!user) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="flex items-center justify-center pt-32">
          <p className="text-muted-foreground">
            {language === 'ar' ? 'سجل دخولك لعرض الجدول' : 'Sign in to view your schedule'}
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="flex items-center justify-center pt-32">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Navbar />
      <main className="container mx-auto px-4 pt-24 max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-6">
          <h1 className="font-display text-4xl md:text-5xl text-foreground mb-2">
            {language === 'ar' ? 'الجدول اليومي' : 'DAILY SCHEDULE'}
          </h1>
          <p className="text-muted-foreground">
            {language === 'ar' ? 'تابع تمارينك وغذاءك يومياً' : 'Track your workouts & nutrition daily'}
          </p>
        </motion.div>

        {/* Tab Toggle */}
        <div className="flex justify-center mb-6">
          <div className="flex bg-card/80 rounded-xl p-1 gap-1 border border-border/50">
            <button onClick={() => setViewTab('workout')}
              className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                viewTab === 'workout' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}>
              <Dumbbell className="w-4 h-4" />
              {language === 'ar' ? 'التمارين' : 'Workouts'}
            </button>
            <button onClick={() => setViewTab('nutrition')}
              className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                viewTab === 'nutrition' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}>
              <UtensilsCrossed className="w-4 h-4" />
              {language === 'ar' ? 'التغذية' : 'Nutrition'}
            </button>
          </div>
        </div>

        {/* Week Navigation */}
        <div className="flex items-center justify-between mb-4">
          <Button variant="ghost" size="icon" onClick={() => setWeekOffset(w => w - 1)}>
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <div className="text-center">
            <p className="text-sm font-semibold text-foreground">{formatWeekRange()}</p>
            {weekOffset !== 0 && (
              <button onClick={() => setWeekOffset(0)} className="text-xs text-primary hover:underline">
                {language === 'ar' ? 'العودة لليوم' : 'Back to today'}
              </button>
            )}
          </div>
          <Button variant="ghost" size="icon" onClick={() => setWeekOffset(w => w + 1)}>
            <ChevronRight className="w-5 h-5" />
          </Button>
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7 gap-1.5 mb-6">
          {weekDates.map((date, idx) => {
            const today = isToday(date);
            const selected = idx === selectedDateIdx;
            const hasMatch = getMatchingPlanDay(currentPlan, date) !== null;
            const hasActivity = hasDailyActivity(date);
            return (
              <button
                key={idx}
                onClick={() => setSelectedDateIdx(idx)}
                className={`flex flex-col items-center py-3 px-1 rounded-xl transition-all text-xs ${
                  selected
                    ? 'bg-primary text-primary-foreground shadow-glow'
                    : today
                      ? 'bg-primary/10 text-primary border border-primary/30'
                      : 'bg-card/50 text-muted-foreground hover:bg-card border border-border/20'
                }`}
              >
                <span className="font-medium">{formatDayName(date)}</span>
                <span className={`text-lg font-bold ${selected ? '' : 'text-foreground'}`}>{formatDateShort(date)}</span>
                {!selected && (hasMatch || hasActivity) && (
                  <div className="mt-1 flex items-center gap-1">
                    {hasMatch && <div className="w-1.5 h-1.5 rounded-full bg-primary" />}
                    {hasActivity && <div className="w-1.5 h-1.5 rounded-full bg-accent" />}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Day Content */}
        {currentPlan ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-8">
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-foreground">
                  {language === 'ar' ? currentPlan.title_ar || currentPlan.title : currentPlan.title}
                </h2>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary/20 text-primary">
                  {language === 'ar' ? 'نشط' : 'Active'}
                </span>
              </div>
              {planProgress && (
                <div className="mb-5">
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                    <span>{language === 'ar' ? 'التقدم' : 'Progress'}</span>
                    <span>
                      {planProgress.completedItems}/{planProgress.totalItems} · {planProgress.percent}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-secondary/60 overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${planProgress.percent}%` }} />
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    {language === 'ar'
                      ? `المتبقي ${planProgress.remaining}%`
                      : `${planProgress.remaining}% remaining`}
                  </div>
                </div>
              )}

              {dailyProgress && dailyProgress.total > 0 && (
                <div className="mb-5">
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                    <span>{language === 'ar' ? 'تقدم اليوم' : 'Daily Progress'}</span>
                    <span>
                      {dailyProgress.completed}/{dailyProgress.total} · {dailyProgress.percent}%
                    </span>
                  </div>
                  <Progress value={dailyProgress.percent} className="h-2" />
                  <div className="mt-2 text-xs text-muted-foreground">
                    {language === 'ar'
                      ? `تاريخ اليوم: ${selectedLogDate}`
                      : `Today: ${selectedLogDate}`}
                  </div>
                </div>
              )}

              <AnimatePresence mode="wait">
                <motion.div
                  key={`${viewTab}-${selectedDateIdx}-${weekOffset}`}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="space-y-3"
                >
                  {matchingDay ? (
                    <>
                      <p className="text-sm text-muted-foreground mb-3">
                        {language === 'ar' ? matchingDay.day.dayAr || matchingDay.day.day : matchingDay.day.day}
                      </p>

                      {/* Exercises */}
                      {matchingDay.day.exercises?.map((ex, exIdx) => {
                        const done = isCompleted(matchingDay.index, exIdx, currentPlan.id);
                        return (
                          <button
                            key={`ex-${exIdx}`}
                            onClick={() => toggleCompletion(matchingDay.index, exIdx, currentPlan.id)}
                            className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-start ${
                              done ? 'bg-primary/10 border-primary/30' : 'bg-card/30 border-border/30 hover:bg-card/50'
                            }`}
                          >
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${
                              done ? 'bg-primary border-primary' : 'border-muted-foreground/40'
                            }`}>
                              {done && <Check className="w-3.5 h-3.5 text-primary-foreground" />}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <Dumbbell className="w-3.5 h-3.5 text-primary/70" />
                                <p className={`font-medium ${done ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
                                  {language === 'ar' ? ex.nameAr || ex.name : ex.name}
                                </p>
                              </div>
                              {ex.sets && <p className="text-xs text-muted-foreground mt-0.5">{ex.sets} × {ex.reps}</p>}
                            </div>
                          </button>
                        );
                      })}

                      {/* Meals */}
                      {matchingDay.day.meals?.map((meal, mIdx) => {
                        const idx = (matchingDay.day.exercises?.length || 0) + mIdx;
                        const done = isCompleted(matchingDay.index, idx, currentPlan.id);
                        return (
                          <button
                            key={`meal-${mIdx}`}
                            onClick={() => toggleCompletion(matchingDay.index, idx, currentPlan.id)}
                            className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-start ${
                              done ? 'bg-primary/10 border-primary/30' : 'bg-card/30 border-border/30 hover:bg-card/50'
                            }`}
                          >
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${
                              done ? 'bg-primary border-primary' : 'border-muted-foreground/40'
                            }`}>
                              {done && <Check className="w-3.5 h-3.5 text-primary-foreground" />}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <UtensilsCrossed className="w-3.5 h-3.5 text-accent-foreground/70" />
                                <p className={`font-medium ${done ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
                                  {language === 'ar' ? meal.nameAr || meal.name : meal.name}
                                </p>
                                {meal.calories && <span className="text-xs text-muted-foreground">({meal.calories} cal)</span>}
                              </div>
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {language === 'ar' ? meal.descriptionAr || meal.description : meal.description}
                              </p>
                            </div>
                          </button>
                        );
                      })}

                      {/* Rest Day */}
                      {(!matchingDay.day.exercises?.length && !matchingDay.day.meals?.length) && (
                        <div className="text-center py-8 text-muted-foreground">
                          <Calendar className="w-10 h-10 mx-auto mb-3 opacity-50" />
                          <p>{language === 'ar' ? 'يوم راحة 😴' : 'Rest Day 😴'}</p>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Calendar className="w-10 h-10 mx-auto mb-3 opacity-50" />
                      <p>{language === 'ar' ? 'لا يوجد خطة لهذا اليوم' : 'No plan for this day'}</p>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        ) : (
          <div className="glass-card rounded-2xl p-10 text-center mb-8">
            {viewTab === 'workout' ? (
              <Dumbbell className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            ) : (
              <UtensilsCrossed className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            )}
            <p className="text-muted-foreground mb-4">
              {viewTab === 'workout'
                ? (language === 'ar' ? 'ما عندك جدول تمارين. اسأل المدرب الذكي يعملك جدول!' : "No workout schedule. Ask AI Coach to create one!")
                : (language === 'ar' ? 'ما عندك نظام غذائي. اسأل المدرب الذكي يعملك نظام!' : "No nutrition plan. Ask AI Coach to create one!")}
            </p>
            <Button variant="hero" onClick={() => window.location.href = '/coach'}>
              {language === 'ar' ? 'اسأل المدرب' : 'Ask AI Coach'}
            </Button>
          </div>
        )}

        <div className="glass-card rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">
              {language === 'ar' ? 'ملاحظات اليوم' : 'Daily Log'}
            </h3>
            <span className="text-xs text-muted-foreground">{selectedLogDate}</span>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-2">
                {language === 'ar' ? 'شو تمرنت اليوم؟' : 'What did you train today?'}
              </label>
              <Textarea
                value={logDraft.workout_notes}
                onChange={(e) => setLogDraft(prev => ({ ...prev, workout_notes: e.target.value }))}
                placeholder={language === 'ar' ? 'اكتب تفاصيل التمرين...' : 'Add workout notes...'}
                className="bg-secondary/40 border-border"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-2">
                {language === 'ar' ? 'شو أكلت اليوم؟' : 'How was your nutrition today?'}
              </label>
              <Textarea
                value={logDraft.nutrition_notes}
                onChange={(e) => setLogDraft(prev => ({ ...prev, nutrition_notes: e.target.value }))}
                placeholder={language === 'ar' ? 'اكتب ملاحظات التغذية...' : 'Add nutrition notes...'}
                className="bg-secondary/40 border-border"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-2">
                {language === 'ar' ? 'مزاجك/طاقتك اليوم' : 'Mood / Energy'}
              </label>
              <Input
                value={logDraft.mood}
                onChange={(e) => setLogDraft(prev => ({ ...prev, mood: e.target.value }))}
                placeholder={language === 'ar' ? 'مثال: طاقة عالية، مرهق...' : 'e.g. High energy, tired...'}
                className="bg-secondary/40 border-border"
              />
            </div>

            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {language === 'ar'
                  ? 'هذه الملاحظات تساعد المدرب الذكي على فهم تقدمك اليومي.'
                  : 'These notes help the AI coach track your daily progress.'}
              </p>
              <Button variant="hero" size="sm" onClick={saveDailyLog} disabled={savingLog}>
                {savingLog
                  ? (language === 'ar' ? 'جارٍ الحفظ...' : 'Saving...')
                  : (language === 'ar' ? 'حفظ' : 'Save')}
              </Button>
            </div>
          </div>
        </div>

        {/* All Plans */}
        {(viewTab === 'workout' ? workoutPlans : nutritionPlans).length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-foreground">
              {language === 'ar' ? 'جميع الخطط' : 'All Plans'}
            </h3>
            <div className="space-y-3">
              {(viewTab === 'workout' ? workoutPlans : nutritionPlans).map(plan => (
                <div key={plan.id} className="glass-card rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">
                      {language === 'ar' ? plan.title_ar || plan.title : plan.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(plan.created_at).toLocaleDateString(language === 'ar' ? 'ar' : 'en')}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {!plan.is_active && (
                      <Button size="sm" variant="outline" onClick={() => activatePlan(plan)}>
                        {language === 'ar' ? 'تفعيل' : 'Activate'}
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => deletePlan(plan.id)}>
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}


