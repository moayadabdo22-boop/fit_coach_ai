-- Production-grade schema for AI Fitness Coach (Supabase/PostgreSQL)
-- Notes:
-- - References Supabase auth.users (UUID)
-- - Uses pgcrypto for gen_random_uuid()
-- - Adjust policies/RLS in Supabase UI as needed

create extension if not exists "pgcrypto";

-- USERS & PROFILE
create table if not exists public.user_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  gender text check (gender in ('male','female','other')) default 'other',
  birth_date date,
  height_cm numeric(6,2),
  weight_kg numeric(6,2),
  body_fat_pct numeric(5,2),
  fitness_level text check (fitness_level in ('beginner','intermediate','advanced')) default 'beginner',
  goal_primary text,
  locale text default 'en',
  timezone text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_user_profiles_goal on public.user_profiles(goal_primary);

-- GOALS
create table if not exists public.goals (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  description text
);

create table if not exists public.user_goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  goal_id uuid not null references public.goals(id) on delete restrict,
  priority int default 1,
  created_at timestamptz not null default now(),
  unique (user_id, goal_id)
);

create index if not exists idx_user_goals_user on public.user_goals(user_id);

-- HEALTH CONDITIONS
create table if not exists public.health_conditions (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  risk_level int default 1,
  description text
);

create table if not exists public.user_conditions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  condition_id uuid not null references public.health_conditions(id) on delete restrict,
  severity text,
  notes text,
  created_at timestamptz not null default now(),
  unique (user_id, condition_id)
);

create index if not exists idx_user_conditions_user on public.user_conditions(user_id);

-- ALLERGIES
create table if not exists public.allergens (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null
);

create table if not exists public.user_allergies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  allergen_id uuid not null references public.allergens(id) on delete restrict,
  severity text,
  created_at timestamptz not null default now(),
  unique (user_id, allergen_id)
);

create index if not exists idx_user_allergies_user on public.user_allergies(user_id);

-- USER PREFERENCES
create table if not exists public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  diet_style text,
  favorite_foods text[],
  disliked_foods text[],
  workout_time text,
  equipment_available text[],
  avoid_equipment text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id)
);

-- NUTRITION DB
create table if not exists public.foods (
  id uuid primary key default gen_random_uuid(),
  source text,
  source_id text,
  name text not null,
  brand text,
  serving_size_g numeric(8,2),
  calories numeric(8,2),
  protein_g numeric(8,2),
  carbs_g numeric(8,2),
  fat_g numeric(8,2),
  fiber_g numeric(8,2),
  sugar_g numeric(8,2),
  sodium_mg numeric(10,2),
  glycemic_index numeric(5,2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_foods_name on public.foods using gin (to_tsvector('simple', name));
create index if not exists idx_foods_source on public.foods(source, source_id);

create table if not exists public.nutrients (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  unit text not null
);

create table if not exists public.food_nutrients (
  id uuid primary key default gen_random_uuid(),
  food_id uuid not null references public.foods(id) on delete cascade,
  nutrient_id uuid not null references public.nutrients(id) on delete restrict,
  amount numeric(12,4) not null,
  unique (food_id, nutrient_id)
);

create index if not exists idx_food_nutrients_food on public.food_nutrients(food_id);

create table if not exists public.food_allergens (
  id uuid primary key default gen_random_uuid(),
  food_id uuid not null references public.foods(id) on delete cascade,
  allergen_id uuid not null references public.allergens(id) on delete restrict,
  unique (food_id, allergen_id)
);

-- MEAL PLANS
create table if not exists public.meal_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  goal_id uuid references public.goals(id) on delete set null,
  daily_calories numeric(10,2),
  macro_distribution jsonb,
  is_active boolean default true,
  start_date date,
  end_date date,
  created_at timestamptz not null default now()
);

create index if not exists idx_meal_plans_user on public.meal_plans(user_id);

create table if not exists public.meals (
  id uuid primary key default gen_random_uuid(),
  meal_plan_id uuid not null references public.meal_plans(id) on delete cascade,
  day_of_week int check (day_of_week between 0 and 6),
  meal_time text,
  name text,
  notes text
);

create index if not exists idx_meals_plan on public.meals(meal_plan_id);

create table if not exists public.meal_items (
  id uuid primary key default gen_random_uuid(),
  meal_id uuid not null references public.meals(id) on delete cascade,
  food_id uuid not null references public.foods(id) on delete restrict,
  servings numeric(8,2) default 1,
  notes text
);

-- EXERCISE DB
create table if not exists public.muscle_groups (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null
);

create table if not exists public.equipment (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null
);

create table if not exists public.exercises (
  id uuid primary key default gen_random_uuid(),
  source text,
  source_id text,
  name text not null,
  difficulty text,
  met numeric(6,2),
  equipment_id uuid references public.equipment(id) on delete set null,
  description text,
  media_url text,
  created_at timestamptz not null default now()
);

create index if not exists idx_exercises_name on public.exercises using gin (to_tsvector('simple', name));

create table if not exists public.exercise_muscles (
  id uuid primary key default gen_random_uuid(),
  exercise_id uuid not null references public.exercises(id) on delete cascade,
  muscle_group_id uuid not null references public.muscle_groups(id) on delete restrict,
  is_primary boolean default true,
  unique (exercise_id, muscle_group_id)
);

-- WORKOUT PLANS
create table if not exists public.workout_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  goal_id uuid references public.goals(id) on delete set null,
  periodization text,
  is_active boolean default true,
  start_date date,
  end_date date,
  created_at timestamptz not null default now()
);

create index if not exists idx_workout_plans_user on public.workout_plans(user_id);

create table if not exists public.workout_days (
  id uuid primary key default gen_random_uuid(),
  workout_plan_id uuid not null references public.workout_plans(id) on delete cascade,
  day_of_week int check (day_of_week between 0 and 6),
  name text
);

create table if not exists public.workout_items (
  id uuid primary key default gen_random_uuid(),
  workout_day_id uuid not null references public.workout_days(id) on delete cascade,
  exercise_id uuid not null references public.exercises(id) on delete restrict,
  sets int,
  reps int,
  duration_min numeric(6,2),
  intensity text,
  notes text
);

-- USER PROGRESS LOGS
create table if not exists public.user_progress_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  log_date date not null,
  weight_kg numeric(6,2),
  body_fat_pct numeric(5,2),
  sleep_hours numeric(4,2),
  calories_in numeric(8,2),
  calories_out numeric(8,2),
  notes text,
  created_at timestamptz not null default now(),
  unique (user_id, log_date)
);

create index if not exists idx_progress_user_date on public.user_progress_logs(user_id, log_date desc);

-- PERFORMANCE METRICS
create table if not exists public.performance_metrics (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  metric_date date not null,
  strength_score numeric(8,2),
  endurance_score numeric(8,2),
  recovery_score numeric(8,2),
  mobility_score numeric(8,2),
  created_at timestamptz not null default now(),
  unique (user_id, metric_date)
);

-- AI RECOMMENDATION LOGS
create table if not exists public.ai_recommendation_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  request_snapshot jsonb not null,
  response_payload jsonb not null,
  feedback_score int,
  created_at timestamptz not null default now()
);

create index if not exists idx_ai_logs_user on public.ai_recommendation_logs(user_id, created_at desc);

-- CHAT MEMORY
create table if not exists public.chat_memory (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  conversation_id text not null,
  role text check (role in ('user','assistant','system')) not null,
  content text not null,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_chat_memory_user_conv on public.chat_memory(user_id, conversation_id, created_at);

-- GAMIFICATION
create table if not exists public.gamification_points (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  points int not null default 0,
  level int not null default 1,
  updated_at timestamptz not null default now(),
  unique (user_id)
);

create table if not exists public.achievements (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  description text
);

create table if not exists public.user_achievements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  achievement_id uuid not null references public.achievements(id) on delete restrict,
  awarded_at timestamptz not null default now(),
  unique (user_id, achievement_id)
);

create table if not exists public.user_streaks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  current_streak int default 0,
  longest_streak int default 0,
  last_activity_date date
);

-- NOTIFICATIONS
create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  body text,
  status text check (status in ('queued','sent','read')) default 'queued',
  scheduled_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_notifications_user_status on public.notifications(user_id, status);

-- USER FEEDBACK
create table if not exists public.user_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  context text,
  rating int check (rating between 1 and 5),
  comment text,
  created_at timestamptz not null default now()
);

