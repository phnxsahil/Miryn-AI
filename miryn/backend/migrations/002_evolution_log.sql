-- Identity evolution log
CREATE TABLE IF NOT EXISTS identity_evolution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    identity_id UUID NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    field_changed VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    trigger_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS identity_evolution_log_user_created_idx
ON identity_evolution_log (user_id, created_at DESC);
