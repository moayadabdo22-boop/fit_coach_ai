import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Dumbbell, Home as HomeIcon } from 'lucide-react';
import { Navbar } from '@/components/layout/Navbar';
import { AnatomyBody, advancedToGroupMap } from '@/components/workout/AnatomyBody';
import { ExerciseCard } from '@/components/workout/ExerciseCard';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { getExercisesByFilters } from '@/data/exercises';
import { bilingualLabel } from '@/lib/text';

export function WorkoutsPage() {
  const { t, language } = useLanguage();
  const { profile } = useUser();

  const [selectedMuscles, setSelectedMuscles] = useState<string[]>([]);
  const [locationFilter, setLocationFilter] = useState<string | null>(profile?.location || null);
  const [goalFilter, setGoalFilter] = useState<string | null>(profile?.goal || null);
  const [genderFilter, setGenderFilter] = useState<'male' | 'female' | null>(
    profile?.gender === 'male' || profile?.gender === 'female' ? profile.gender : null
  );

  const toggleMuscle = (muscleId: string) => {
    setSelectedMuscles((prev) =>
      prev.includes(muscleId) ? prev.filter((m) => m !== muscleId) : [...prev, muscleId]
    );
  };

  const muscleNames: Record<string, string> = {
    'muscle.chest': t('muscle.chest'),
    'muscle.back': t('muscle.back'),
    'muscle.shoulders': t('muscle.shoulders'),
    'muscle.biceps': t('muscle.biceps'),
    'muscle.triceps': t('muscle.triceps'),
    'muscle.abs': t('muscle.abs'),
    'muscle.quads': t('muscle.quads'),
    'muscle.hamstrings': t('muscle.hamstrings'),
    'muscle.glutes': t('muscle.glutes'),
    'muscle.calves': t('muscle.calves'),
  };

  // Map selected muscles (which may be advanced/detailed) to exercise group filters
  const mappedMuscles = selectedMuscles.map(m => advancedToGroupMap[m] || m);
  const uniqueMuscles = [...new Set(mappedMuscles)];

  const exercises = getExercisesByFilters(uniqueMuscles, goalFilter, locationFilter, genderFilter);
  const genderLabel = bilingualLabel('Gender', 'الجنس', language);
  const placeLabel = bilingualLabel('Place', 'المكان', language);
  const goalLabel = bilingualLabel('Goal', 'الهدف', language);

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <Navbar />

      <main className="container mx-auto px-4 pt-24">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <h1 className="font-display text-4xl md:text-5xl text-foreground mb-2">{t('workouts.title')}</h1>
          <p className="text-muted-foreground">{t('workouts.subtitle')}</p>
        </motion.div>

        {/* Body Selector */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-6 mb-8"
        >
          <AnatomyBody selectedMuscles={selectedMuscles} onMuscleToggle={toggleMuscle} muscleNames={muscleNames} />
        </motion.div>

        {/* Filters */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="flex flex-wrap gap-3 mb-8 justify-center"
        >
          {/* Gender Filter */}
          <div className="flex items-center gap-1 bg-card/50 rounded-xl p-1 border border-border/30">
            <span className="text-xs text-muted-foreground px-2">{genderLabel}:</span>
            {[{ val: null, label: bilingualLabel('All', 'الكل', language) }, { val: 'male', label: bilingualLabel('Male', 'ذكر', language) }, { val: 'female', label: bilingualLabel('Female', 'أنثى', language) }].map(opt => (
              <Button key={String(opt.val)} variant={genderFilter === opt.val ? 'default' : 'ghost'} size="sm"
                onClick={() => setGenderFilter(opt.val)}
              >{opt.label}</Button>
            ))}
          </div>

          {/* Location Filter */}
          <div className="flex items-center gap-1 bg-card/50 rounded-xl p-1 border border-border/30">
            <span className="text-xs text-muted-foreground px-2">{placeLabel}:</span>
            {[{ val: null, label: bilingualLabel('All', 'الكل', language) }, { val: 'home', label: bilingualLabel('Home', 'البيت', language), icon: HomeIcon }, { val: 'gym', label: bilingualLabel('Gym', 'الجيم', language), icon: Dumbbell }].map(opt => (
              <Button key={String(opt.val)} variant={locationFilter === opt.val ? 'default' : 'ghost'} size="sm"
                onClick={() => setLocationFilter(opt.val)}
              >
                {opt.icon && <opt.icon className="w-3.5 h-3.5 mr-1" />}
                {opt.label}
              </Button>
            ))}
          </div>

          {/* Goal Filter */}
          <div className="flex items-center gap-1 bg-card/50 rounded-xl p-1 border border-border/30">
            <span className="text-xs text-muted-foreground px-2">{goalLabel}:</span>
            {[{ val: null, label: bilingualLabel('All', 'الكل', language) }, { val: 'bulking', label: bilingualLabel('Build Muscle', 'بناء عضلات', language) }, { val: 'cutting', label: bilingualLabel('Lose Weight', 'إنقاص الوزن', language) }, { val: 'fitness', label: bilingualLabel('General Fitness', 'لياقة عامة', language) }].map(opt => (
              <Button key={String(opt.val)} variant={goalFilter === opt.val ? 'default' : 'ghost'} size="sm"
                onClick={() => setGoalFilter(opt.val)}
              >{opt.label}</Button>
            ))}
          </div>
        </motion.div>

        {/* Results Count */}
        <div className="text-center mb-6">
          <span className="text-sm text-muted-foreground">
            {exercises.length} {t('workouts.exercises')}
          </span>
        </div>

        {/* Exercises Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {exercises.map((exercise, index) => (
            <motion.div key={exercise.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 + index * 0.02 }}>
              <ExerciseCard exercise={exercise} selectedGender={genderFilter} />
            </motion.div>
          ))}
        </div>

        {exercises.length === 0 && (
          <div className="text-center py-16">
            <Dumbbell className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{t('workouts.noResults')}</p>
          </div>
        )}
      </main>
    </div>
  );
}
