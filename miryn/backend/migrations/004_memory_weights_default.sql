ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS memory_weights JSONB DEFAULT '{"beliefs": 0.33, "emotions": 0.33, "facts": 0.17, "goals": 0.17}'::jsonb;

ALTER TABLE identities
  ALTER COLUMN memory_weights SET DEFAULT '{"beliefs": 0.33, "emotions": 0.33, "facts": 0.17, "goals": 0.17}'::jsonb;
