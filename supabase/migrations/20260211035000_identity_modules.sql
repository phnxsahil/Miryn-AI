-- Identity module tables
CREATE TABLE IF NOT EXISTS identity_beliefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic VARCHAR(255) NOT NULL,
  belief TEXT NOT NULL,
  confidence FLOAT DEFAULT 0.5,
  evidence JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS identity_beliefs_identity_id_idx ON identity_beliefs(identity_id);
CREATE INDEX IF NOT EXISTS identity_beliefs_user_id_idx ON identity_beliefs(user_id);

CREATE TABLE IF NOT EXISTS identity_open_loops (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'open',
  importance INT DEFAULT 1,
  last_mentioned TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS identity_open_loops_identity_id_idx ON identity_open_loops(identity_id);
CREATE INDEX IF NOT EXISTS identity_open_loops_user_id_idx ON identity_open_loops(user_id);

CREATE TABLE IF NOT EXISTS identity_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  pattern_type VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  signals JSONB DEFAULT '{}',
  confidence FLOAT DEFAULT 0.5,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS identity_patterns_identity_id_idx ON identity_patterns(identity_id);
CREATE INDEX IF NOT EXISTS identity_patterns_user_id_idx ON identity_patterns(user_id);

CREATE TABLE IF NOT EXISTS identity_emotions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  primary_emotion VARCHAR(100) NOT NULL,
  intensity FLOAT DEFAULT 0.5,
  secondary_emotions JSONB DEFAULT '[]',
  context JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS identity_emotions_identity_id_idx ON identity_emotions(identity_id);
CREATE INDEX IF NOT EXISTS identity_emotions_user_id_idx ON identity_emotions(user_id);

CREATE TABLE IF NOT EXISTS identity_conflicts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id UUID REFERENCES identities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  statement TEXT NOT NULL,
  conflict_with TEXT NOT NULL,
  severity FLOAT DEFAULT 0.5,
  resolved BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS identity_conflicts_identity_id_idx ON identity_conflicts(identity_id);
CREATE INDEX IF NOT EXISTS identity_conflicts_user_id_idx ON identity_conflicts(user_id);

-- Encryption columns for messages
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS content_encrypted TEXT;
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS metadata_encrypted TEXT;
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS encryption_version INT DEFAULT 1;
