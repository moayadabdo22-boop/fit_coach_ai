-- Feedback table for plan evaluation
create extension if not exists "pgcrypto";

create table if not exists public.plan_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan_id text not null,
  plan_type text not null check (plan_type in ('workout','nutrition')),
  difficulty int4,
  satisfaction int4,
  adherence numeric,
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists plan_feedback_user_idx on public.plan_feedback(user_id);
create index if not exists plan_feedback_plan_idx on public.plan_feedback(plan_id);

alter table public.plan_feedback enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'plan_feedback' and policyname = 'Users can view own plan feedback'
  ) then
    create policy "Users can view own plan feedback" on public.plan_feedback
      for select using (auth.uid() = user_id);
  end if;

  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'plan_feedback' and policyname = 'Users can create own plan feedback'
  ) then
    create policy "Users can create own plan feedback" on public.plan_feedback
      for insert with check (auth.uid() = user_id);
  end if;
end $$;
