-- Create users_extended table
CREATE TABLE IF NOT EXISTS public.users_extended (
  id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  goal TEXT,
  fitness_level TEXT CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
  chronic_diseases TEXT[] DEFAULT ARRAY[]::TEXT[],
  allergies TEXT[] DEFAULT ARRAY[]::TEXT[],
  preferred_language TEXT CHECK (preferred_language IN ('en', 'ar_fusha', 'ar_jordanian')) DEFAULT 'en',
  rest_days TEXT[] DEFAULT ARRAY[]::TEXT[],
  target_calories INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create workout_plans table
CREATE TABLE IF NOT EXISTS public.workout_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  plan_json JSONB NOT NULL,
  start_date DATE,
  end_date DATE,
  approved BOOLEAN DEFAULT FALSE,
  approved_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, start_date)
);

-- Create nutrition_plans table
CREATE TABLE IF NOT EXISTS public.nutrition_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  plan_json JSONB NOT NULL,
  daily_calories INTEGER,
  start_date DATE,
  end_date DATE,
  approved BOOLEAN DEFAULT FALSE,
  approved_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, start_date)
);

-- Create daily_tracking table
CREATE TABLE IF NOT EXISTS public.daily_tracking (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  date DATE NOT NULL,
  workout_completed BOOLEAN DEFAULT FALSE,
  meals_completed BOOLEAN DEFAULT FALSE,
  workout_notes TEXT,
  meals_notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, date)
);

-- Create chat_memory table (long-term memory)
CREATE TABLE IF NOT EXISTS public.chat_memory (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  conversation_id TEXT NOT NULL,
  message_index INTEGER,
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_extended_id ON public.users_extended(id);
CREATE INDEX IF NOT EXISTS idx_workout_plans_user_id ON public.workout_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_plans_user_id ON public.nutrition_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_tracking_user_id_date ON public.daily_tracking(user_id, date);
CREATE INDEX IF NOT EXISTS idx_chat_memory_user_id_conversation ON public.chat_memory(user_id, conversation_id);

-- Enable RLS
ALTER TABLE public.users_extended ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_memory ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own extended profile" ON public.users_extended
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own extended profile" ON public.users_extended
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own extended profile" ON public.users_extended
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can view own workout plans" ON public.workout_plans
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own workout plans" ON public.workout_plans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workout plans" ON public.workout_plans
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own nutrition plans" ON public.nutrition_plans
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own nutrition plans" ON public.nutrition_plans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own nutrition plans" ON public.nutrition_plans
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own daily tracking" ON public.daily_tracking
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own daily tracking" ON public.daily_tracking
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own daily tracking" ON public.daily_tracking
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own chat memory" ON public.chat_memory
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own chat memory" ON public.chat_memory
  FOR INSERT WITH CHECK (auth.uid() = user_id);
