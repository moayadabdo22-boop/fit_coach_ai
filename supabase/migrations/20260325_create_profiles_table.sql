-- Ensure profiles table exists (used by frontend) and add speaking_style
create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id uuid not null default gen_random_uuid() primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null default '',
  age integer not null default 25,
  gender text not null default 'male' check (gender in ('male','female')),
  weight numeric not null default 70,
  height numeric not null default 175,
  goal text not null default 'fitness' check (goal in ('bulking','cutting','fitness')),
  location text not null default 'home' check (location in ('home','gym')),
  onboarding_completed boolean not null default false,
  speaking_style jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id)
);

alter table public.profiles add column if not exists speaking_style jsonb;

alter table public.profiles enable row level security;
