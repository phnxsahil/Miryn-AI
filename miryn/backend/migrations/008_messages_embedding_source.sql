ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS embedding_source VARCHAR(50) DEFAULT 'gemini';

ALTER TABLE messages
  ALTER COLUMN embedding_source SET DEFAULT 'gemini';
