
-- Add chronic_conditions column to profiles
ALTER TABLE public.profiles ADD COLUMN chronic_conditions text NOT NULL DEFAULT '';
