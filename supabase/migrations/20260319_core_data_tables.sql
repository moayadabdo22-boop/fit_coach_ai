-- Supabase Migration: Plans, Progress, and Tracking Tables
-- File: 20260319_core_data_tables.sql
-- Description: Create tables for plans history, daily progress, and tracking

-- 1. PLANS HISTORY TABLE
CREATE TABLE IF NOT EXISTS plans_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_type VARCHAR(50) NOT NULL CHECK (plan_type IN ('workout', 'nutrition', 'combined')),
  plan_content JSONB NOT NULL, -- Full plan structure (exercises, meals, schedule)
  plan_name VARCHAR(255),
  duration_days INT NOT NULL CHECK (duration_days > 0),
  difficulty VARCHAR(20) CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
  focus_areas TEXT[], -- Tags: 'strength', 'cardio', 'flexibility', 'weight_loss', etc
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  completion_rate DECIMAL(5,2) DEFAULT 0 CHECK (completion_rate >= 0 AND completion_rate <= 100),
  completed_workouts INT DEFAULT 0,
  total_workouts INT DEFAULT 0,
  feedback TEXT,
  notes TEXT,
  is_active BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, start_date) -- Prevent overlapping active plans
);

CREATE INDEX idx_plans_user_date ON plans_history(user_id, created_at DESC);
CREATE INDEX idx_plans_active ON plans_history(user_id, is_active) WHERE is_active = TRUE;

-- 2. DAILY PROGRESS TABLE
CREATE TABLE IF NOT EXISTS daily_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  log_date DATE NOT NULL,
  
  -- Physical Metrics
  weight DECIMAL(6,2), -- kg
  body_measurements JSONB, -- {"chest": 95.5, "waist": 78.0, "arms": 32.5}
  
  -- Nutrition
  calories_consumed INT,
  calories_burned INT,
  protein_grams DECIMAL(6,2),
  carbs_grams DECIMAL(6,2),
  fat_grams DECIMAL(6,2),
  water_intake DECIMAL(5,2), -- liters
  
  -- Activity
  sleep_hours DECIMAL(3,1),
  exercise_duration INT, -- minutes
  steps_count INT,
  heart_rate_avg INT, -- bpm
  
  -- Logging Status
  mood VARCHAR(20) CHECK (mood IN ('excellent', 'good', 'neutral', 'poor')),
  energy_level INT CHECK (energy_level >= 1 AND energy_level <= 10), -- 1-10
  completed_workouts INT DEFAULT 0,
  meals_logged INT DEFAULT 0,
  
  -- Notes & Observations
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, log_date)
);

CREATE INDEX idx_progress_user_date ON daily_progress(user_id, log_date DESC);
CREATE INDEX idx_progress_weight ON daily_progress(user_id, log_date) WHERE weight IS NOT NULL;

-- 3. COMPLETED WORKOUTS TABLE
CREATE TABLE IF NOT EXISTS completed_workouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  workout_date DATE NOT NULL,
  workout_plan_id UUID REFERENCES plans_history(id) ON DELETE SET NULL,
  
  -- Exercise Details
  exercise_name VARCHAR(255) NOT NULL,
  muscle_groups TEXT[], -- ['chest', 'triceps', 'shoulders']
  
  -- Performance Metrics
  sets INT,
  reps INT,
  weight DECIMAL(6,2), -- kg
  duration_minutes INT,
  rest_seconds INT,
  
  -- Quality Indicators
  intensity VARCHAR(20) CHECK (intensity IN ('light', 'moderate', 'high', 'max')),
  difficulty_rating INT CHECK (difficulty_rating >= 1 AND difficulty_rating <= 10),
  form_quality INT CHECK (form_quality >= 1 AND form_quality <= 10),
  completed BOOLEAN DEFAULT TRUE,
  
  -- Meta
  video_form_url TEXT, -- Link to form correction video if needed
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, workout_date, exercise_name)
);

CREATE INDEX idx_completed_workouts_user ON completed_workouts(user_id, workout_date DESC);
CREATE INDEX idx_completed_workouts_muscle ON completed_workouts(user_id) 
  WHERE muscle_groups IS NOT NULL;

-- 4. COMPLETED MEALS TABLE
CREATE TABLE IF NOT EXISTS completed_meals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  meal_date DATE NOT NULL,
  meal_plan_id UUID REFERENCES plans_history(id) ON DELETE SET NULL,
  
  -- Meal Info
  meal_name VARCHAR(255) NOT NULL,
  meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner', 'evening_snack')),
  cuisine_type VARCHAR(100),
  
  -- Nutrition Data
  calories INT,
  protein DECIMAL(6,2),
  carbs DECIMAL(6,2),
  fat DECIMAL(6,2),
  fiber DECIMAL(6,2),
  sodium INT, -- mg
  
  -- Ingredients & Allergens
  ingredients TEXT[],
  allergens TEXT[],
  
  -- Quality Metrics
  portion_size VARCHAR(100),
  preparation_difficulty VARCHAR(20),
  taste_rating INT CHECK (taste_rating >= 1 AND taste_rating <= 10),
  completed BOOLEAN DEFAULT TRUE,
  
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, meal_date, meal_name, meal_type)
);

CREATE INDEX idx_completed_meals_user ON completed_meals(user_id, meal_date DESC);
CREATE INDEX idx_completed_meals_type ON completed_meals(user_id, meal_type);

-- Enable RLS
ALTER TABLE plans_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE completed_workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE completed_meals ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own plan history" ON plans_history
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own plans" ON plans_history
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own plans" ON plans_history
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own progress" ON daily_progress
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own progress" ON daily_progress
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own progress" ON daily_progress
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own workouts" ON completed_workouts
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workouts" ON completed_workouts
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own meals" ON completed_meals
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own meals" ON completed_meals
  FOR INSERT WITH CHECK (auth.uid() = user_id);
