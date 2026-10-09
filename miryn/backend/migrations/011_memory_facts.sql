CREATE TABLE IF NOT EXISTS memory_facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  fact TEXT NOT NULL,
  fact_key VARCHAR(64) NOT NULL,
  category VARCHAR(40) NOT NULL,
  importance FLOAT NOT NULL DEFAULT 0.5,
  emotional_weight FLOAT NOT NULL DEFAULT 0,
  source_message_id UUID,
  extractor VARCHAR(16) NOT NULL DEFAULT 'heuristic',
  mention_count INT NOT NULL DEFAULT 1,
  status VARCHAR(16) NOT NULL DEFAULT 'active',
  first_seen_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memory_facts_user_imp_idx
  ON memory_facts(user_id, status, importance DESC);

CREATE UNIQUE INDEX IF NOT EXISTS memory_facts_user_key_idx
  ON memory_facts(user_id, fact_key)
  WHERE status = 'active';
