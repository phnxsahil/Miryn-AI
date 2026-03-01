ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS preset VARCHAR(50);

ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS memory_weights JSONB DEFAULT '{}'::jsonb;
