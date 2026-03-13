import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { Exercise } from '@/data/exercises';
import { getExerciseVideoUrl, isLocalExerciseVideo } from '@/data/exerciseVideoResolver';
import { bilingualLabel, repairMojibake } from '@/lib/text';

interface ExerciseCardProps {
  exercise: Exercise;
  selectedGender?: 'male' | 'female' | null;
}

const muscleLabelsEn: Record<string, string> = {
  chest: 'Chest',
  back: 'Back',
  shoulders: 'Shoulders',
  biceps: 'Biceps',
  triceps: 'Triceps',
  abs: 'Abs',
  quads: 'Quads',
  hamstrings: 'Hamstrings',
  glutes: 'Glutes',
  calves: 'Calves',
};

const muscleLabelsAr: Record<string, string> = {
  chest: 'الصدر',
  back: 'الظهر',
  shoulders: 'الأكتاف',
  biceps: 'البايسبس',
  triceps: 'الترايسبس',
  abs: 'البطن',
  quads: 'الفخذ الأمامي',
  hamstrings: 'الفخذ الخلفي',
  glutes: 'المؤخرة',
  calves: 'السمانة',
};

export function ExerciseCard({ exercise, selectedGender = null }: ExerciseCardProps) {
  const { language, t } = useLanguage();
  const [showVideo, setShowVideo] = useState<boolean>(false);
  const resolvedVideoUrl = getExerciseVideoUrl(exercise, selectedGender);
  const localVideo = isLocalExerciseVideo(resolvedVideoUrl);
  const hasVideo = localVideo && resolvedVideoUrl.length > 0;

  const englishName = repairMojibake(exercise.name);
  const arabicName = repairMojibake(exercise.nameAr || exercise.name);
  const englishDescription = repairMojibake(exercise.description);
  const arabicDescription = repairMojibake(exercise.descriptionAr || exercise.description);

  const name = bilingualLabel(englishName, arabicName, language);
  const description = bilingualLabel(englishDescription, arabicDescription, language);
  const noVideoLabel = bilingualLabel('No video', 'لا يوجد فيديو', language);
  const setsLabel = bilingualLabel('Sets', 'مجموعات', language);
  const repsLabel = bilingualLabel('Reps', 'تكرارات', language);

  const muscleLabel = bilingualLabel(
    muscleLabelsEn[exercise.muscle] || t(`muscle.${exercise.muscle}`),
    muscleLabelsAr[exercise.muscle] || t(`muscle.${exercise.muscle}`),
    language
  );

  const locationLabel =
    exercise.location === 'home'
      ? bilingualLabel('Home', 'البيت', language)
      : exercise.location === 'gym'
        ? bilingualLabel('Gym', 'الجيم', language)
        : bilingualLabel('Both', 'كلاهما', language);

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-xl overflow-hidden group hover:border-primary/50 transition-all duration-300"
      >
        {/* Video Thumbnail */}
        <div
          className={`relative h-40 bg-secondary overflow-hidden ${hasVideo ? 'cursor-pointer' : 'cursor-not-allowed opacity-80'}`}
          onClick={() => {
            if (hasVideo) {
              setShowVideo(true);
            }
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-t from-card to-transparent z-10" />
          <div className="absolute inset-0 flex items-center justify-center z-20">
            {hasVideo ? (
              <div className="w-14 h-14 rounded-full bg-primary/90 flex items-center justify-center group-hover:scale-110 transition-transform shadow-glow">
                <Play className="w-6 h-6 text-primary-foreground ml-1" />
              </div>
            ) : (
              <span className="text-xs px-3 py-1 rounded-full bg-background/70 text-muted-foreground border border-border/50">
                {noVideoLabel}
              </span>
            )}
          </div>
          {hasVideo ? (
            <video
              src={resolvedVideoUrl}
              className="w-full h-full object-cover"
              muted
              playsInline
              preload="metadata"
            />
          ) : (
            <img
              src="/placeholder.svg"
              alt={name}
              className="w-full h-full object-cover"
            />
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          <h3 className="font-semibold text-lg text-foreground mb-1">{name}</h3>
          <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{description}</p>

          {/* Stats */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <span className="text-primary font-bold">{exercise.sets}</span>
              <span className="text-muted-foreground">{setsLabel}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-primary font-bold">{exercise.reps}</span>
              <span className="text-muted-foreground">{repsLabel}</span>
            </div>
          </div>

          {/* Tags */}
          <div className="flex gap-2 mt-3 flex-wrap">
            <span className="px-2 py-1 text-xs rounded-full bg-primary/20 text-primary">
              {muscleLabel}
            </span>
            <span className="px-2 py-1 text-xs rounded-full bg-accent/20 text-accent">
              {locationLabel}
            </span>
          </div>
        </div>
      </motion.div>

      {/* Video Modal */}
      {showVideo && hasVideo && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-sm p-4"
          onClick={() => setShowVideo(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative w-full max-w-3xl aspect-video bg-card rounded-xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 z-10 bg-background/50 hover:bg-background/80"
              onClick={() => setShowVideo(false)}
            >
              <X className="w-5 h-5" />
            </Button>
            {localVideo ? (
              <video
                src={resolvedVideoUrl}
                className="w-full h-full object-contain bg-black"
                controls
                autoPlay
                playsInline
              />
            ) : (
              <iframe
                src={`${resolvedVideoUrl}?autoplay=1`}
                className="w-full h-full"
                allow="autoplay; encrypted-media"
                allowFullScreen
                title={name}
              />
            )}
          </motion.div>
        </div>
      )}
    </>
  );
}
