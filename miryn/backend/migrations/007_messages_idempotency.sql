ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS messages_user_idempotency_key_uq
  ON messages (user_id, idempotency_key);
