-- Add extended training fields to profiles
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS fitness_level TEXT NOT NULL DEFAULT 'beginner' CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
  ADD COLUMN IF NOT EXISTS training_days_per_week INTEGER NOT NULL DEFAULT 3,
  ADD COLUMN IF NOT EXISTS equipment TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS injuries TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS activity_level TEXT NOT NULL DEFAULT 'moderate' CHECK (activity_level IN ('low', 'moderate', 'high')),
  ADD COLUMN IF NOT EXISTS dietary_preferences TEXT NOT NULL DEFAULT '';
