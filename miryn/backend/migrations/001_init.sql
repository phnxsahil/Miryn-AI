-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Identities (versioned user personality)
CREATE TABLE IF NOT EXISTS identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version INT DEFAULT 1,
    state VARCHAR(50) DEFAULT 'onboarding',
    traits JSONB DEFAULT '{}',
    values JSONB DEFAULT '{}',
    beliefs JSONB DEFAULT '[]',
    open_loops JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, version)
);

  CREATE INDEX IF NOT EXISTS identities_user_id_idx ON identities(user_id);

-- Identity beliefs
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

-- Identity open loops
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

-- Identity patterns
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

-- Identity emotions
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

-- Identity conflicts
CREATE TABLE IF NOT EXISTS identity_conflicts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
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

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS conversations_user_id_idx ON conversations(user_id);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT,
    embedding vector(384),
    metadata JSONB DEFAULT '{}',
    importance_score FLOAT DEFAULT 0.5,
    memory_tier VARCHAR(20) NOT NULL DEFAULT 'episodic' CHECK (memory_tier IN ('transient', 'episodic', 'core')),
    delete_at TIMESTAMP,
    content_encrypted TEXT,
    metadata_encrypted TEXT,
    encryption_version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS messages_embedding_idx
ON messages USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS messages_user_id_idx ON messages(user_id);
CREATE INDEX IF NOT EXISTS messages_user_tier_idx ON messages(user_id, memory_tier);
CREATE INDEX IF NOT EXISTS messages_delete_at_idx ON messages(delete_at);

-- Backfill columns for existing deployments
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS memory_tier VARCHAR(20) NOT NULL DEFAULT 'episodic' CHECK (memory_tier IN ('transient', 'episodic', 'core'));
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS delete_at TIMESTAMP;
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS content_encrypted TEXT;
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS metadata_encrypted TEXT;
ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS encryption_version INT DEFAULT 1;

-- Onboarding responses
CREATE TABLE IF NOT EXISTS onboarding_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question VARCHAR(500) NOT NULL,
  answer TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION match_messages(
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  user_id_filter uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  content_encrypted text,
  metadata_encrypted text,
  importance_score float,
  created_at timestamp,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  IF query_embedding IS NULL THEN
    RETURN;
  END IF;
  RETURN QUERY
  SELECT
    scored.id,
    scored.content,
    scored.metadata,
    scored.content_encrypted,
    scored.metadata_encrypted,
    scored.importance_score,
    scored.created_at,
    scored.similarity
  FROM (
    SELECT
      m.id,
      m.content,
      m.metadata,
      m.content_encrypted,
      m.metadata_encrypted,
      m.importance_score,
      m.created_at,
      1 - (m.embedding <=> query_embedding) AS similarity
    FROM messages m
    WHERE m.user_id = user_id_filter
      AND m.memory_tier = 'core'
      AND (m.delete_at IS NULL OR m.delete_at > NOW())
      AND m.embedding IS NOT NULL
  ) AS scored
  WHERE scored.similarity > match_threshold
  ORDER BY scored.similarity DESC
  LIMIT match_count;
END;
$$;

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    path VARCHAR(255),
    method VARCHAR(20),
    status_code INT,
    ip VARCHAR(64),
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memory summaries
CREATE TABLE IF NOT EXISTS memory_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tool runs
CREATE TABLE IF NOT EXISTS tool_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    request JSONB DEFAULT '{}',
    code TEXT,
    result TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS tool_runs_user_id_idx ON tool_runs(user_id);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    payload JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS notifications_user_id_idx ON notifications(user_id);
