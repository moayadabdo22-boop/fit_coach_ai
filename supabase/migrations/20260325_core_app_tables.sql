-- Core app tables + RLS policies for plans, completions, logs, and chat

create table if not exists public.workout_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'AI Workout Plan',
  title_ar text not null default '',
  plan_data jsonb not null default '[]'::jsonb,
  is_active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.workout_plans add column if not exists title text;
alter table public.workout_plans add column if not exists title_ar text;
alter table public.workout_plans add column if not exists plan_data jsonb;
alter table public.workout_plans add column if not exists is_active boolean default false;
alter table public.workout_plans add column if not exists created_at timestamptz default now();
alter table public.workout_plans add column if not exists updated_at timestamptz default now();

create table if not exists public.workout_completions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan_id uuid not null references public.workout_plans(id) on delete cascade,
  day_index integer not null default 0,
  exercise_index integer not null default 0,
  completed boolean not null default true,
  log_date date not null default current_date,
  completed_at timestamptz not null default now()
);

alter table public.workout_completions add column if not exists log_date date default current_date;
create index if not exists idx_workout_completions_user_date
  on public.workout_completions(user_id, log_date);

create table if not exists public.daily_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  log_date date not null,
  workout_notes text not null default '',
  nutrition_notes text not null default '',
  mood text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, log_date)
);

create table if not exists public.chat_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.chat_conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create or replace function public.update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql set search_path = public;

drop trigger if exists update_workout_plans_updated_at on public.workout_plans;
create trigger update_workout_plans_updated_at
  before update on public.workout_plans
  for each row execute function public.update_updated_at_column();

drop trigger if exists update_daily_logs_updated_at on public.daily_logs;
create trigger update_daily_logs_updated_at
  before update on public.daily_logs
  for each row execute function public.update_updated_at_column();

drop trigger if exists update_chat_conversations_updated_at on public.chat_conversations;
create trigger update_chat_conversations_updated_at
  before update on public.chat_conversations
  for each row execute function public.update_updated_at_column();

alter table public.workout_plans enable row level security;
alter table public.workout_completions enable row level security;
alter table public.daily_logs enable row level security;
alter table public.chat_conversations enable row level security;
alter table public.chat_messages enable row level security;

drop policy if exists app_select_workout_plans on public.workout_plans;
create policy app_select_workout_plans on public.workout_plans
  for select using (auth.uid() = user_id);
drop policy if exists app_insert_workout_plans on public.workout_plans;
create policy app_insert_workout_plans on public.workout_plans
  for insert with check (auth.uid() = user_id);
drop policy if exists app_update_workout_plans on public.workout_plans;
create policy app_update_workout_plans on public.workout_plans
  for update using (auth.uid() = user_id);
drop policy if exists app_delete_workout_plans on public.workout_plans;
create policy app_delete_workout_plans on public.workout_plans
  for delete using (auth.uid() = user_id);

drop policy if exists app_select_workout_completions on public.workout_completions;
create policy app_select_workout_completions on public.workout_completions
  for select using (auth.uid() = user_id);
drop policy if exists app_insert_workout_completions on public.workout_completions;
create policy app_insert_workout_completions on public.workout_completions
  for insert with check (auth.uid() = user_id);
drop policy if exists app_delete_workout_completions on public.workout_completions;
create policy app_delete_workout_completions on public.workout_completions
  for delete using (auth.uid() = user_id);

drop policy if exists app_select_daily_logs on public.daily_logs;
create policy app_select_daily_logs on public.daily_logs
  for select using (auth.uid() = user_id);
drop policy if exists app_insert_daily_logs on public.daily_logs;
create policy app_insert_daily_logs on public.daily_logs
  for insert with check (auth.uid() = user_id);
drop policy if exists app_update_daily_logs on public.daily_logs;
create policy app_update_daily_logs on public.daily_logs
  for update using (auth.uid() = user_id);

drop policy if exists app_select_chat_conversations on public.chat_conversations;
create policy app_select_chat_conversations on public.chat_conversations
  for select using (auth.uid() = user_id);
drop policy if exists app_insert_chat_conversations on public.chat_conversations;
create policy app_insert_chat_conversations on public.chat_conversations
  for insert with check (auth.uid() = user_id);
drop policy if exists app_update_chat_conversations on public.chat_conversations;
create policy app_update_chat_conversations on public.chat_conversations
  for update using (auth.uid() = user_id);
drop policy if exists app_delete_chat_conversations on public.chat_conversations;
create policy app_delete_chat_conversations on public.chat_conversations
  for delete using (auth.uid() = user_id);

drop policy if exists app_select_chat_messages on public.chat_messages;
create policy app_select_chat_messages on public.chat_messages
  for select using (auth.uid() = user_id);
drop policy if exists app_insert_chat_messages on public.chat_messages;
create policy app_insert_chat_messages on public.chat_messages
  for insert with check (auth.uid() = user_id);
