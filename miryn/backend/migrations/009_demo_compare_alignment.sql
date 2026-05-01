CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    full_name TEXT,
    avatar_url TEXT,
    primary_goal TEXT,
    selected_traits TEXT,
    communication_style TEXT,
    preferred_depth TEXT,
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS drift_score DOUBLE PRECISION DEFAULT 0;

ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS notification_preferences TEXT;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS data_retention TEXT;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
