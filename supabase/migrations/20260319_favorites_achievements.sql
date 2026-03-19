-- Supabase Migration: Favorites, Achievements, and User Preferences
-- File: 20260319_favorites_achievements.sql
-- Description: Create tables for user favorites and gamification features

-- 1. FAVORITE MEALS TABLE
CREATE TABLE IF NOT EXISTS favorite_meals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  meal_name VARCHAR(255) NOT NULL,
  cuisine_type VARCHAR(100),
  meal_type VARCHAR(20) CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
  
  -- Nutritional Info
  calories INT,
  protein DECIMAL(6,2),
  carbs DECIMAL(6,2),
  fat DECIMAL(6,2),
  
  -- Preparation
  prep_time_minutes INT,
  cooking_time_minutes INT,
  difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'advanced')),
  
  -- Recipe
  ingredients TEXT[],
  instructions TEXT,
  allergens TEXT[],
  
  -- Meta
  recipe_url TEXT,
  image_url TEXT,
  rating INT CHECK (rating >= 1 AND rating <= 5),
  times_prepared INT DEFAULT 0,
  personal_notes TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, meal_name)
);

CREATE INDEX idx_favorite_meals_user ON favorite_meals(user_id);
CREATE INDEX idx_favorite_meals_cuisine ON favorite_meals(user_id, cuisine_type);

-- 2. FAVORITE EXERCISES TABLE
CREATE TABLE IF NOT EXISTS favorite_exercises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  exercise_name VARCHAR(255) NOT NULL,
  muscle_groups TEXT[] NOT NULL, -- ['chest', 'triceps', 'shoulders']
  secondary_muscles TEXT[], -- ['core', 'stabilizers']
  
  -- Difficulty & Equipment
  difficulty VARCHAR(20) CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
  equipment_required TEXT[], -- ['dumbbell', 'barbell', 'none']
  alternative_equipment TEXT[],
  
  -- Performance Tracking
  personal_best_weight DECIMAL(6,2),
  personal_best_reps INT,
  personal_best_date DATE,
  
  -- Instructions
  description TEXT,
  form_tips TEXT,
  common_mistakes TEXT,
  
  -- Media & Resources
  demo_video_url TEXT,
  demo_image_url TEXT,
  
  -- Preferences
  rating INT CHECK (rating >= 1 AND rating <= 5),
  times_done INT DEFAULT 0,
  is_warm_up BOOLEAN DEFAULT FALSE,
  personal_notes TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, exercise_name)
);

CREATE INDEX idx_favorite_exercises_user ON favorite_exercises(user_id);
CREATE INDEX idx_favorite_exercises_muscle ON favorite_exercises(user_id) 
  WHERE muscle_groups IS NOT NULL;

-- 3. USER ACHIEVEMENTS TABLE
CREATE TABLE IF NOT EXISTS user_achievements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  achievement_type VARCHAR(100) NOT NULL,
  achievement_key VARCHAR(100) NOT NULL, -- Machine-readable: 'first_workout', '7day_streak'
  achievement_name VARCHAR(255),
  description TEXT,
  
  -- Badge Details
  badge_icon_url TEXT,
  badge_rarity VARCHAR(20) CHECK (badge_rarity IN ('common', 'rare', 'epic', 'legendary')),
  
  -- Reward
  points_earned INT DEFAULT 0,
  unlock_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Progression
  progress_value DECIMAL(10,2), -- e.g., "12" for 12-day streak
  progress_target DECIMAL(10,2), -- e.g., "30" for 30-day goal
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, achievement_key)
);

CREATE INDEX idx_achievements_user ON user_achievements(user_id, unlock_date DESC);
CREATE INDEX idx_achievements_type ON user_achievements(achievement_type);

-- 4. USER MILESTONES TABLE
CREATE TABLE IF NOT EXISTS user_milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  milestone_type VARCHAR(100) NOT NULL, -- 'weight_loss', 'workout_count', 'calorie_goal'
  milestone_name VARCHAR(255),
  description TEXT,
  
  -- Progress Tracking
  target_value DECIMAL(10,2) NOT NULL,
  current_value DECIMAL(10,2) DEFAULT 0,
  progress_percentage DECIMAL(5,2) DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
  unit VARCHAR(50), -- 'kg', 'count', 'cal', 'days'
  
  -- Status
  achieved BOOLEAN DEFAULT FALSE,
  achieved_date TIMESTAMP,
  started_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deadline_date DATE,
  
  -- Reward
  reward_points INT DEFAULT 0,
  
  -- Display
  icon_url TEXT,
  difficulty_rating INT CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_milestones_user ON user_milestones(user_id, achieved DESC);
CREATE INDEX idx_milestones_active ON user_milestones(user_id, achieved) 
  WHERE achieved = FALSE AND deadline_date IS NOT NULL;

-- 5. STREAKS TABLE
CREATE TABLE IF NOT EXISTS streaks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  streak_type VARCHAR(50) NOT NULL, -- 'gym_visits', 'meal_logging', 'app_access'
  CHECK (streak_type IN ('gym_visits', 'meal_logging', 'app_access', 'plan_adherence')),
  
  -- Streak Data
  current_streak INT DEFAULT 0,
  best_streak INT DEFAULT 0,
  current_streak_start_date DATE,
  best_streak_start_date DATE,
  best_streak_end_date DATE,
  
  -- Activity Tracking
  last_activity_date DATE,
  activities_count INT DEFAULT 0,
  
  -- Freeze Protection
  freeze_tokens INT DEFAULT 0, -- Remaining freeze uses this month
  max_freezes_per_month INT DEFAULT 2,
  last_freeze_used_date DATE,
  
  -- Rewards
  total_points_earned INT DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, streak_type)
);

CREATE INDEX idx_streaks_user ON streaks(user_id);
CREATE INDEX idx_streaks_type ON streaks(streak_type);

-- 6. USER POINTS TABLE
CREATE TABLE IF NOT EXISTS user_points (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Point Totals
  points_total INT DEFAULT 0,
  points_month INT DEFAULT 0, -- Reset monthly
  points_week INT DEFAULT 0,   -- Reset weekly
  
  -- Level & Experience
  level INT DEFAULT 1 CHECK (level >= 1 AND level <= 50),
  experience BIGINT DEFAULT 0,
  next_level_experience BIGINT, -- XP needed for next level
  
  -- Achievement Percentage
  lifetime_points INT DEFAULT 0,
  
  -- Updates
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id)
);

CREATE INDEX idx_user_points_user ON user_points(user_id);
CREATE INDEX idx_user_points_level ON user_points(level DESC);

-- 7. POINT TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS point_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  points INT NOT NULL,
  transaction_type VARCHAR(100) NOT NULL, 
  -- 'workout_complete', 'meal_logged', 'achievement_unlocked', 'streak_bonus', 'challenge_completed'
  
  related_id UUID, -- Reference to: achievement, workout, meal, etc
  description TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_point_transactions_user ON point_transactions(user_id, created_at DESC);
CREATE INDEX idx_point_transactions_type ON point_transactions(transaction_type);

-- Enable RLS
ALTER TABLE favorite_meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorite_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE streaks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE point_transactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own favorites" ON favorite_meals
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own favorites" ON favorite_meals
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own favorites" ON favorite_meals
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own favorites" ON favorite_meals
  FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for other tables
CREATE POLICY "Users can view own achievements" ON user_achievements
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own milestones" ON user_milestones
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own streaks" ON streaks
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own points" ON user_points
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own transactions" ON point_transactions
  FOR SELECT USING (auth.uid() = user_id);
