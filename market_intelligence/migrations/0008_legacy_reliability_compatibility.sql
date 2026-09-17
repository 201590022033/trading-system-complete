-- Some early version-4 installs predated reliability_outcomes. Preserve all
-- existing tables/data while completing that additive schema on upgrade.
CREATE TABLE IF NOT EXISTS reliability_outcomes (
 reliability_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, scope_key TEXT NOT NULL,
 horizon TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(reliability_id));
CREATE INDEX IF NOT EXISTS idx_reliability_scope ON reliability_outcomes(source_id,scope_key,horizon);
