import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface BodySelectorProps {
  selectedMuscles: string[];
  onMuscleToggle: (muscleId: string) => void;
  muscleNames: Record<string, string>;
}

type BodyView = 'front' | 'back';

export function BodySelector({ selectedMuscles, onMuscleToggle, muscleNames }: BodySelectorProps) {
  const [view, setView] = useState<BodyView>('front');

  const isActive = (muscle: string) => selectedMuscles.includes(muscle);

  const muscleStyle = (muscle: string) => ({
    fill: isActive(muscle) ? 'url(#activeGradient)' : 'hsl(220, 15%, 50%)',
    stroke: isActive(muscle) ? 'hsl(188, 100%, 60%)' : 'hsl(220, 15%, 35%)',
    strokeWidth: isActive(muscle) ? 1.5 : 0.8,
    cursor: 'pointer' as const,
    transition: 'all 0.3s ease',
    filter: isActive(muscle) ? 'drop-shadow(0 0 8px hsla(188, 100%, 48%, 0.6))' : 'none',
    opacity: isActive(muscle) ? 1 : 0.75,
  });

  const bodyFill = 'hsl(220, 12%, 28%)';
  const bodyStroke = 'hsl(220, 12%, 38%)';

  const muscles = [
    { id: 'chest', name: muscleNames['muscle.chest'] || 'Chest' },
    { id: 'shoulders', name: muscleNames['muscle.shoulders'] || 'Shoulders' },
    { id: 'biceps', name: muscleNames['muscle.biceps'] || 'Biceps' },
    { id: 'triceps', name: muscleNames['muscle.triceps'] || 'Triceps' },
    { id: 'abs', name: muscleNames['muscle.abs'] || 'Abs' },
    { id: 'back', name: muscleNames['muscle.back'] || 'Back' },
    { id: 'quads', name: muscleNames['muscle.quads'] || 'Quads' },
    { id: 'hamstrings', name: muscleNames['muscle.hamstrings'] || 'Hamstrings' },
    { id: 'glutes', name: muscleNames['muscle.glutes'] || 'Glutes' },
    { id: 'calves', name: muscleNames['muscle.calves'] || 'Calves' },
  ];

  return (
    <div className="flex flex-col items-center gap-6">
      {/* View Toggle */}
      <div className="flex bg-secondary rounded-xl p-1 gap-1">
        <button
          onClick={() => setView('front')}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
            view === 'front'
              ? 'bg-primary text-primary-foreground shadow-button'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          {muscleNames['muscle.chest'] ? 'أمام' : 'Front'}
        </button>
        <button
          onClick={() => setView('back')}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
            view === 'back'
              ? 'bg-primary text-primary-foreground shadow-button'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          {muscleNames['muscle.back'] ? 'خلف' : 'Back'}
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 items-center justify-center">
        {/* Body SVG */}
        <div className="relative">
          <svg viewBox="0 0 220 480" className="w-48 h-[26rem] md:w-60 md:h-[32rem]">
            <defs>
              <linearGradient id="activeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="hsl(188, 100%, 45%)" />
                <stop offset="100%" stopColor="hsl(200, 100%, 55%)" />
              </linearGradient>
              <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="hsl(220, 12%, 32%)" />
                <stop offset="100%" stopColor="hsl(220, 12%, 24%)" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Base Body Silhouette */}
            <g fill="url(#bodyGradient)" stroke={bodyStroke} strokeWidth="1">
              {/* Head */}
              <ellipse cx="110" cy="38" rx="24" ry="28" />
              {/* Neck */}
              <rect x="100" y="64" width="20" height="16" rx="3" />

              {/* Torso */}
              <path d="M68,80 Q75,78 85,80 L135,80 Q145,78 152,80 L158,170 L155,175 L65,175 L62,170 Z" />

              {/* Upper Arms */}
              <path d="M62,82 Q50,85 44,95 L38,140 Q36,148 40,150 L50,148 Q54,146 56,140 L62,95 Z" />
              <path d="M158,82 Q170,85 176,95 L182,140 Q184,148 180,150 L170,148 Q166,146 164,140 L158,95 Z" />

              {/* Forearms */}
              <path d="M38,150 Q34,155 32,165 L28,200 Q26,208 30,210 L38,208 Q42,206 44,200 L48,165 Q50,155 48,150 Z" />
              <path d="M180,150 Q184,155 186,165 L190,200 Q192,208 188,210 L180,208 Q176,206 174,200 L170,165 Q168,155 170,150 Z" />

              {/* Hands */}
              <ellipse cx="30" cy="216" rx="8" ry="10" />
              <ellipse cx="190" cy="216" rx="8" ry="10" />

              {/* Hips */}
              <path d="M65,175 L155,175 L158,195 Q155,205 150,210 L70,210 Q65,205 62,195 Z" />

              {/* Upper Legs */}
              <path d="M70,210 Q68,215 66,225 L62,310 Q60,320 64,322 L88,322 Q92,320 90,310 L94,225 Q95,215 93,210 Z" />
              <path d="M150,210 Q152,215 154,225 L158,310 Q160,320 156,322 L132,322 Q128,320 130,310 L126,225 Q125,215 127,210 Z" />

              {/* Lower Legs */}
              <path d="M64,322 L88,322 Q90,330 88,345 L86,410 Q85,420 82,425 L70,425 Q67,420 66,410 L64,345 Q62,330 64,322 Z" />
              <path d="M156,322 L132,322 Q130,330 132,345 L134,410 Q135,420 138,425 L150,425 Q153,420 154,410 L156,345 Q158,330 156,322 Z" />

              {/* Feet */}
              <path d="M66,425 L84,425 Q88,428 90,432 L90,440 Q88,445 82,446 L68,446 Q62,445 60,440 L60,432 Q62,428 66,425 Z" />
              <path d="M154,425 L136,425 Q132,428 130,432 L130,440 Q132,445 138,446 L152,446 Q158,445 160,440 L160,432 Q158,428 154,425 Z" />
            </g>

            {/* Clickable Muscle Overlays */}
            {view === 'front' ? (
              <g>
                {/* Shoulders - Front */}
                <ellipse cx="62" cy="88" rx="14" ry="12" style={muscleStyle('shoulders')} onClick={() => onMuscleToggle('shoulders')} />
                <ellipse cx="158" cy="88" rx="14" ry="12" style={muscleStyle('shoulders')} onClick={() => onMuscleToggle('shoulders')} />

                {/* Chest */}
                <path d="M78,88 Q95,85 110,88 Q110,105 100,112 Q90,116 78,110 Z" style={muscleStyle('chest')} onClick={() => onMuscleToggle('chest')} />
                <path d="M142,88 Q125,85 110,88 Q110,105 120,112 Q130,116 142,110 Z" style={muscleStyle('chest')} onClick={() => onMuscleToggle('chest')} />

                {/* Biceps */}
                <ellipse cx="50" cy="118" rx="8" ry="20" style={muscleStyle('biceps')} onClick={() => onMuscleToggle('biceps')} />
                <ellipse cx="170" cy="118" rx="8" ry="20" style={muscleStyle('biceps')} onClick={() => onMuscleToggle('biceps')} />

                {/* Abs */}
                <g onClick={() => onMuscleToggle('abs')} style={{ cursor: 'pointer' as const }}>
                  {/* Upper abs */}
                  <rect x="96" y="115" width="12" height="14" rx="2" style={muscleStyle('abs')} />
                  <rect x="112" y="115" width="12" height="14" rx="2" style={muscleStyle('abs')} />
                  {/* Mid abs */}
                  <rect x="96" y="132" width="12" height="14" rx="2" style={muscleStyle('abs')} />
                  <rect x="112" y="132" width="12" height="14" rx="2" style={muscleStyle('abs')} />
                  {/* Lower abs */}
                  <rect x="96" y="149" width="12" height="14" rx="2" style={muscleStyle('abs')} />
                  <rect x="112" y="149" width="12" height="14" rx="2" style={muscleStyle('abs')} />
                </g>

                {/* Quads */}
                <path d="M72,218 Q70,240 68,270 Q66,295 70,310 L86,310 Q90,295 88,270 Q86,240 88,218 Z" style={muscleStyle('quads')} onClick={() => onMuscleToggle('quads')} />
                <path d="M148,218 Q150,240 152,270 Q154,295 150,310 L134,310 Q130,295 132,270 Q134,240 132,218 Z" style={muscleStyle('quads')} onClick={() => onMuscleToggle('quads')} />

                {/* Calves - Front */}
                <ellipse cx="76" cy="370" rx="9" ry="30" style={muscleStyle('calves')} onClick={() => onMuscleToggle('calves')} />
                <ellipse cx="144" cy="370" rx="9" ry="30" style={muscleStyle('calves')} onClick={() => onMuscleToggle('calves')} />
              </g>
            ) : (
              <g>
                {/* Shoulders - Back */}
                <ellipse cx="62" cy="88" rx="14" ry="12" style={muscleStyle('shoulders')} onClick={() => onMuscleToggle('shoulders')} />
                <ellipse cx="158" cy="88" rx="14" ry="12" style={muscleStyle('shoulders')} onClick={() => onMuscleToggle('shoulders')} />

                {/* Back (Lats + Traps) */}
                <path d="M75,85 Q90,82 110,84 Q130,82 145,85 L148,100 Q145,130 140,155 Q130,165 110,168 Q90,165 80,155 Q75,130 72,100 Z" style={muscleStyle('back')} onClick={() => onMuscleToggle('back')} />

                {/* Triceps */}
                <ellipse cx="50" cy="118" rx="8" ry="20" style={muscleStyle('triceps')} onClick={() => onMuscleToggle('triceps')} />
                <ellipse cx="170" cy="118" rx="8" ry="20" style={muscleStyle('triceps')} onClick={() => onMuscleToggle('triceps')} />

                {/* Glutes */}
                <ellipse cx="85" cy="194" rx="18" ry="16" style={muscleStyle('glutes')} onClick={() => onMuscleToggle('glutes')} />
                <ellipse cx="135" cy="194" rx="18" ry="16" style={muscleStyle('glutes')} onClick={() => onMuscleToggle('glutes')} />

                {/* Hamstrings */}
                <path d="M72,218 Q70,240 68,270 Q66,295 70,310 L86,310 Q90,295 88,270 Q86,240 88,218 Z" style={muscleStyle('hamstrings')} onClick={() => onMuscleToggle('hamstrings')} />
                <path d="M148,218 Q150,240 152,270 Q154,295 150,310 L134,310 Q130,295 132,270 Q134,240 132,218 Z" style={muscleStyle('hamstrings')} onClick={() => onMuscleToggle('hamstrings')} />

                {/* Calves - Back */}
                <ellipse cx="76" cy="370" rx="10" ry="32" style={muscleStyle('calves')} onClick={() => onMuscleToggle('calves')} />
                <ellipse cx="144" cy="370" rx="10" ry="32" style={muscleStyle('calves')} onClick={() => onMuscleToggle('calves')} />
              </g>
            )}
          </svg>
        </div>

        {/* Muscle Selection Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 gap-2 w-full lg:w-auto">
          {muscles.map((muscle) => (
            <motion.button
              key={muscle.id}
              onClick={() => onMuscleToggle(muscle.id)}
              whileTap={{ scale: 0.95 }}
              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 border ${
                selectedMuscles.includes(muscle.id)
                  ? 'bg-primary/15 text-primary border-primary/40 shadow-button'
                  : 'bg-secondary/50 text-secondary-foreground border-border/30 hover:bg-secondary/80 hover:border-border/60'
              }`}
            >
              <span className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  selectedMuscles.includes(muscle.id) ? 'bg-primary' : 'bg-muted-foreground/30'
                }`} />
                {muscle.name}
              </span>
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
}
