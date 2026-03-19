-- Supabase Migration: Notifications, Feedback, and Admin/Audit Tables
-- File: 20260319_notifications_admin.sql
-- Description: Create tables for notifications, user feedback, and admin features

-- 1. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Notification Content
  notification_type VARCHAR(50) NOT NULL,
  -- 'reminder', 'achievement', 'alert', 'message', 'suggestion', 'challenge', 'milestone'
  
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  
  -- Deep Link
  action_url VARCHAR(500),
  action_type VARCHAR(50), -- 'open_plan', 'start_workout', 'log_meal', etc
  
  -- Media
  icon_url TEXT,
  image_url TEXT,
  
  -- Status
  is_read BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  read_at TIMESTAMP,
  
  -- Delivery
  delivery_method VARCHAR(50) CHECK (delivery_method IN ('push', 'email', 'in_app', 'sms')),
  
  -- Priority & Scheduling
  priority INT DEFAULT 1 CHECK (priority BETWEEN 1 AND 5), -- 1 = low, 5 = critical
  scheduled_for TIMESTAMP, -- For scheduled notifications
  
  -- Metadata
  source_type VARCHAR(100), -- 'system', 'ai_coach', 'user_action', 'admin'
  source_id UUID, -- Reference to source (achievement_id, etc)
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) 
  WHERE is_read = FALSE;

-- 2. USER FEEDBACK TABLE
CREATE TABLE IF NOT EXISTS user_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Feedback Details
  feedback_type VARCHAR(50) NOT NULL,
  -- 'bug_report', 'feature_request', 'general_feedback', 'complaint'
  
  category VARCHAR(100), -- 'ui', 'performance', 'feature_request', 'workout', 'nutrition'
  
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  
  -- Rating
  rating INT CHECK (rating >= 1 AND rating <= 5),
  
  -- Attachments
  attachments TEXT[], -- URLs to images, screenshots
  
  -- Status Tracking
  status VARCHAR(20) DEFAULT 'new',
  -- 'new', 'acknowledged', 'in_progress', 'resolved', 'closed', 'declined'
  
  priority VARCHAR(20) DEFAULT 'medium',
  -- 'low', 'medium', 'high', 'critical'
  
  -- Response
  internal_notes TEXT, -- Admin notes
  response TEXT, -- Response to user
  responded_at TIMESTAMP,
  
  -- Metadata
  device_info JSONB, -- Browser, OS, app version
  feature_context VARCHAR(255), -- Which feature was user in
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_user ON user_feedback(user_id, created_at DESC);
CREATE INDEX idx_feedback_status ON user_feedback(status);
CREATE INDEX idx_feedback_type ON user_feedback(feedback_type);

-- 3. PLAN RATINGS TABLE
CREATE TABLE IF NOT EXISTS plan_ratings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES plans_history(id) ON DELETE CASCADE,
  
  -- Overall Rating
  overall_rating INT NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
  
  -- Specific Ratings
  difficulty_rating INT CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),
  effectiveness_rating INT CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),
  enjoyment_rating INT CHECK (enjoyment_rating >= 1 AND enjoyment_rating <= 5),
  sustainability_rating INT CHECK (sustainability_rating >= 1 AND sustainability_rating <= 5),
  
  -- Preferences
  would_repeat BOOLEAN,
  would_recommend BOOLEAN,
  
  -- Feedback
  strengths_comment TEXT,
  improvements_comment TEXT,
  general_comment TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, plan_id)
);

CREATE INDEX idx_plan_ratings_plan ON plan_ratings(plan_id);

-- 4. LEADERBOARD TABLE (Materialized View Helper)
CREATE TABLE IF NOT EXISTS leaderboard_snapshot (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  username VARCHAR(255),
  
  -- Score Data
  points INT NOT NULL,
  level INT NOT NULL,
  current_streak INT NOT NULL,
  
  -- Ranking
  rank INT GENERATED ALWAYS AS IDENTITY,
  percentile DECIMAL(5,2), -- 0-100%
  
  -- Period
  period VARCHAR(20) NOT NULL, -- 'weekly', 'monthly', 'all_time'
  
  -- Region/Cohort (for filtered leaderboards)
  region VARCHAR(100),
  goal_type VARCHAR(100),
  
  snapshot_date DATE DEFAULT CURRENT_DATE,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leaderboard_period_points ON leaderboard_snapshot(period, points DESC);
CREATE INDEX idx_leaderboard_user_period ON leaderboard_snapshot(user_id, period);

-- 5. AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  
  -- Action Details
  action VARCHAR(255) NOT NULL, -- 'profile_updated', 'data_exported', 'plan_created'
  resource_type VARCHAR(100), -- 'profile', 'plan', 'payment'
  resource_id VARCHAR(255),
  
  -- Changes Tracked
  old_value JSONB,
  new_value JSONB,
  
  -- Request Info
  ip_address INET,
  user_agent TEXT,
  http_method VARCHAR(10),
  endpoint VARCHAR(255),
  
  -- Result
  success BOOLEAN,
  error_message TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- 6. DATA CONSENT TABLE
CREATE TABLE IF NOT EXISTS data_consent (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Consent Flags
  marketing_emails BOOLEAN DEFAULT FALSE,
  personalization BOOLEAN DEFAULT TRUE,
  analytics_tracking BOOLEAN DEFAULT TRUE,
  third_party_integration BOOLEAN DEFAULT FALSE,
  health_data_research BOOLEAN DEFAULT FALSE,
  location_tracking BOOLEAN DEFAULT FALSE,
  push_notifications BOOLEAN DEFAULT TRUE,
  
  -- Consent Record
  accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address_at_consent INET,
  
  -- Versions
  privacy_policy_version VARCHAR(50),
  terms_version VARCHAR(50)
);

CREATE INDEX idx_consent_user ON data_consent(user_id);

-- 7. DATA EXPORT REQUESTS TABLE
CREATE TABLE IF NOT EXISTS data_export_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Request Details
  export_type VARCHAR(100), -- 'full', 'health_data', 'activity_only'
  format VARCHAR(20) DEFAULT 'json', -- 'json', 'csv', 'pdf'
  
  -- Status
  status VARCHAR(20) DEFAULT 'pending',
  -- 'pending', 'processing', 'completed', 'failed', 'expired'
  
  -- Files
  file_url TEXT,
  file_size_bytes BIGINT,
  
  -- Expiration
  requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
  
  -- Admin Notes
  error_details TEXT
);

CREATE INDEX idx_export_requests_user ON data_export_requests(user_id, requested_at DESC);
CREATE INDEX idx_export_requests_status ON data_export_requests(status);

-- 8. HEALTH METRICS TABLE (Enhanced from schema v1)
CREATE TABLE IF NOT EXISTS health_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  
  -- Body Composition
  weight DECIMAL(6,2),
  body_fat_percentage DECIMAL(5,2),
  muscle_mass_kg DECIMAL(6,2),
  lean_mass_kg DECIMAL(6,2),
  bone_density DECIMAL(5,2),
  
  -- Cardiovascular
  blood_pressure_systolic INT,
  blood_pressure_diastolic INT,
  resting_heart_rate INT,
  heart_rate_variability DECIMAL(5,2),
  vo2_max DECIMAL(5,2),
  
  -- Metabolic
  metabolic_rate INT,
  bmi DECIMAL(5,2),
  
  -- Flexibilty & Mobility
  sit_and_reach_cm DECIMAL(5,2),
  grip_strength_kg DECIMAL(5,2),
  
  -- Notes
  measurement_method VARCHAR(100), -- 'scale', 'bioimpedance', 'calipers'
  notes TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, metric_date)
);

CREATE INDEX idx_health_metrics_user ON health_metrics(user_id, metric_date DESC);

-- Enable RLS
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_snapshot ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_consent ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_export_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own notifications" ON notifications
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON notifications
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own feedback" ON user_feedback
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert feedback" ON user_feedback
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own ratings" ON plan_ratings
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert ratings" ON plan_ratings
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view public leaderboard" ON leaderboard_snapshot
  FOR SELECT USING (true);

CREATE POLICY "Admin can view audit logs" ON audit_logs
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM auth.users 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Users can view own consent" ON data_consent
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own consent" ON data_consent
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own requests" ON data_export_requests
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own health metrics" ON health_metrics
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert health metrics" ON health_metrics
  FOR INSERT WITH CHECK (auth.uid() = user_id);
