ALTER TABLE memory_facts
  ADD COLUMN IF NOT EXISTS superseded_by UUID REFERENCES memory_facts(id);

CREATE TABLE IF NOT EXISTS memory_fact_supersessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  old_fact_id UUID NOT NULL REFERENCES memory_facts(id),
  new_fact_id UUID NOT NULL REFERENCES memory_facts(id),
  source_message_id UUID,
  corrects JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memory_fact_supersessions_user_idx
  ON memory_fact_supersessions(user_id, created_at DESC);
