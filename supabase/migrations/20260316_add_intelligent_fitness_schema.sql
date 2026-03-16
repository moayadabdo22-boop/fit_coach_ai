-- Extend users_extended with full profile fields
ALTER TABLE public.users_extended
  ADD COLUMN IF NOT EXISTS age INTEGER,
  ADD COLUMN IF NOT EXISTS gender TEXT,
  ADD COLUMN IF NOT EXISTS height_cm NUMERIC,
  ADD COLUMN IF NOT EXISTS weight_kg NUMERIC,
  ADD COLUMN IF NOT EXISTS bmi NUMERIC,
  ADD COLUMN IF NOT EXISTS workout_preference TEXT,
  ADD COLUMN IF NOT EXISTS available_equipment TEXT[] DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS training_days_per_week INTEGER,
  ADD COLUMN IF NOT EXISTS session_duration_minutes INTEGER,
  ADD COLUMN IF NOT EXISTS injuries TEXT[] DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS dietary_preferences TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Exercise catalog table
CREATE TABLE IF NOT EXISTS public.exercise_catalog (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  target_muscles TEXT[] DEFAULT ARRAY[]::TEXT[],
  difficulty TEXT,
  equipment TEXT,
  exercise_type TEXT,
  calories_burned_est INTEGER,
  injury_risk TEXT,
  gender_suitability TEXT,
  beginner_alternative TEXT,
  description TEXT,
  source TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Nutrition catalog table
CREATE TABLE IF NOT EXISTS public.nutrition_catalog (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  category TEXT,
  calories INTEGER,
  protein_g NUMERIC,
  carbs_g NUMERIC,
  fat_g NUMERIC,
  fiber_g NUMERIC,
  sugars_g NUMERIC,
  sodium_mg NUMERIC,
  cholesterol_mg NUMERIC,
  glycemic_index_label TEXT,
  allergens TEXT[] DEFAULT ARRAY[]::TEXT[],
  disease_flags TEXT[] DEFAULT ARRAY[]::TEXT[],
  meal_type TEXT,
  source TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Extend daily_tracking for richer performance data
ALTER TABLE public.daily_tracking
  ADD COLUMN IF NOT EXISTS weight_kg NUMERIC,
  ADD COLUMN IF NOT EXISTS calories_burned INTEGER,
  ADD COLUMN IF NOT EXISTS steps INTEGER,
  ADD COLUMN IF NOT EXISTS sleep_hours NUMERIC,
  ADD COLUMN IF NOT EXISTS avg_heart_rate NUMERIC,
  ADD COLUMN IF NOT EXISTS workout_minutes INTEGER;

-- Performance reports
CREATE TABLE IF NOT EXISTS public.performance_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  report_date DATE NOT NULL,
  report_json JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, report_date)
);

CREATE INDEX IF NOT EXISTS idx_exercise_catalog_name ON public.exercise_catalog(name);
CREATE INDEX IF NOT EXISTS idx_nutrition_catalog_name ON public.nutrition_catalog(name);
CREATE INDEX IF NOT EXISTS idx_performance_reports_user_id ON public.performance_reports(user_id);

ALTER TABLE public.exercise_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_reports ENABLE ROW LEVEL SECURITY;

-- Public read for catalogs
CREATE POLICY "Public read exercise catalog" ON public.exercise_catalog
  FOR SELECT USING (true);
CREATE POLICY "Public read nutrition catalog" ON public.nutrition_catalog
  FOR SELECT USING (true);

-- Users can read own performance reports
CREATE POLICY "Users can view own performance reports" ON public.performance_reports
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own performance reports" ON public.performance_reports
  FOR INSERT WITH CHECK (auth.uid() = user_id);
