-- Persist the LLM extractor's explicit-correction marker on the fact row so
-- retrieval ordering can place a validated correction ahead of the fact it
-- corrects. Ordering metadata only: no status change, no supersession link.
-- Durable supersession stays behind MEMORY_SUPERSESSION_ENABLED.
-- Fernet-encrypted JSON, same shape and protection as
-- memory_fact_supersessions.corrects.
ALTER TABLE memory_facts
  ADD COLUMN IF NOT EXISTS corrects TEXT;
