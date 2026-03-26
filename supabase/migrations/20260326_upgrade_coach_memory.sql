-- Upgrade coach_memory to key/value entries for long-term personalization
create extension if not exists "pgcrypto";

do $$
begin
  if exists (
    select 1
    from information_schema.tables
    where table_schema = 'public'
      and table_name = 'coach_memory'
  ) then
    -- If legacy schema exists (goals/exercise_history columns), rename it.
    if exists (
      select 1
      from information_schema.columns
      where table_schema = 'public'
        and table_name = 'coach_memory'
        and column_name = 'goals'
    ) then
      alter table public.coach_memory rename to coach_memory_legacy;
    end if;
  end if;
end $$;

create table if not exists public.coach_memory (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  key text not null,
  value jsonb,
  importance_score numeric not null default 0.5,
  created_at timestamptz not null default now(),
  unique (user_id, key)
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

-- Migrate legacy data if available
do $$
begin
  if exists (
    select 1
    from information_schema.tables
    where table_schema = 'public'
      and table_name = 'coach_memory_legacy'
  ) then
    insert into public.coach_memory (user_id, key, value, importance_score)
    select user_id, 'goals', goals, 0.8 from public.coach_memory_legacy
    where goals is not null
    on conflict (user_id, key) do nothing;

    insert into public.coach_memory (user_id, key, value, importance_score)
    select user_id, 'exercise_history', exercise_history, 0.7 from public.coach_memory_legacy
    where exercise_history is not null
    on conflict (user_id, key) do nothing;

    insert into public.coach_memory (user_id, key, value, importance_score)
    select user_id, 'speaking_style', speaking_style, 0.6 from public.coach_memory_legacy
    where speaking_style is not null
    on conflict (user_id, key) do nothing;

    insert into public.coach_memory (user_id, key, value, importance_score)
    select user_id, 'notes', notes, 0.4 from public.coach_memory_legacy
    where notes is not null
    on conflict (user_id, key) do nothing;
  end if;
end $$;
