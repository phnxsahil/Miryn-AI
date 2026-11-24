-- Subject provenance for stored facts. Additive and non-destructive:
-- existing rows read as 'unknown' and are never implicitly superseded.
-- No backfill, no UPDATE, no DELETE. Read and written only when
-- MEMORY_SUBJECT_ENABLED is on.
ALTER TABLE memory_facts
  ADD COLUMN IF NOT EXISTS subject VARCHAR(8) NOT NULL DEFAULT 'unknown'
  CHECK (subject IN ('user', 'other', 'unknown'));
