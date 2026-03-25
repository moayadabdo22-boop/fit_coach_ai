-- Coach memory table for long-term personalization
create extension if not exists "pgcrypto";

create table if not exists public.coach_memory (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  goals jsonb,
  exercise_history jsonb,
  speaking_style jsonb,
  notes jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id)
);

alter table public.coach_memory enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'coach_memory' and policyname = 'Users can view own coach memory'
  ) then
    create policy "Users can view own coach memory" on public.coach_memory
      for select using (auth.uid() = user_id);
  end if;

  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'coach_memory' and policyname = 'Users can create own coach memory'
  ) then
    create policy "Users can create own coach memory" on public.coach_memory
      for insert with check (auth.uid() = user_id);
  end if;

  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'coach_memory' and policyname = 'Users can update own coach memory'
  ) then
    create policy "Users can update own coach memory" on public.coach_memory
      for update using (auth.uid() = user_id);
  end if;
end $$;

