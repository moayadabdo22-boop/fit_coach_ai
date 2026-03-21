-- Add allergies column to profiles table
ALTER TABLE public.profiles ADD COLUMN allergies text NOT NULL DEFAULT '';
