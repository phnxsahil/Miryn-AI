-- Shared spend ledger for paid LLM providers (Claude). One row per provider.
-- Amounts are micro-USD (1e-6 USD) so integer math stays exact across workers.
CREATE TABLE IF NOT EXISTS llm_budget (
  provider TEXT PRIMARY KEY,
  spent_micro BIGINT NOT NULL DEFAULT 0,
  reserved_micro BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
