-- High-fidelity SQLite schema for Miryn Demo
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    is_deleted BOOLEAN DEFAULT 0,
    is_verified BOOLEAN DEFAULT 0,
    notification_preferences TEXT,
    data_retention TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT,
    avatar_url TEXT,
    primary_goal TEXT,
    selected_traits TEXT,
    communication_style TEXT,
    preferred_depth TEXT,
    onboarding_completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identities (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    state TEXT,
    traits TEXT,
    "values" TEXT,
    beliefs TEXT,
    open_loops TEXT,
    patterns TEXT,
    emotions TEXT,
    conflicts TEXT,
    preset TEXT,
    memory_weights TEXT,
    drift_score REAL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_evolution_log (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    identity_id TEXT REFERENCES identities(id) ON DELETE CASCADE,
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,
    trigger_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_beliefs (
    id TEXT PRIMARY KEY,
    identity_id TEXT REFERENCES identities(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT,
    belief TEXT,
    confidence REAL,
    evidence TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_conflicts (
    id TEXT PRIMARY KEY,
    identity_id TEXT REFERENCES identities(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    type TEXT,
    description TEXT,
    resolution_status TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_emotions (
    id TEXT PRIMARY KEY,
    identity_id TEXT REFERENCES identities(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    emotion TEXT,
    intensity REAL,
    trigger TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_open_loops (
    id TEXT PRIMARY KEY,
    identity_id TEXT REFERENCES identities(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT,
    status TEXT,
    importance INTEGER,
    last_mentioned TIMESTAMP,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_patterns (
    id TEXT PRIMARY KEY,
    identity_id TEXT REFERENCES identities(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    pattern TEXT,
    frequency INTEGER,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    is_deleted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT,
    content TEXT,
    entities TEXT,
    emotions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS onboarding_responses (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    question TEXT,
    answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    event_type TEXT,
    path TEXT,
    method TEXT,
    status_code INTEGER,
    ip TEXT,
    user_agent TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
