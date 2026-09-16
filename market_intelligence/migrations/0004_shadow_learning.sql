CREATE TABLE IF NOT EXISTS observations (observation_id TEXT PRIMARY KEY, instrument TEXT NOT NULL, observed_at TEXT NOT NULL, horizon TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, source_version TEXT NOT NULL, pipeline_version TEXT NOT NULL, UNIQUE(instrument, observed_at, horizon, source_version, pipeline_version));
CREATE INDEX IF NOT EXISTS idx_observations_time ON observations(observed_at);
CREATE TABLE IF NOT EXISTS shadow_decisions (decision_id TEXT PRIMARY KEY, observation_id TEXT NOT NULL UNIQUE, instrument TEXT NOT NULL, decided_at TEXT NOT NULL, horizon TEXT NOT NULL, action TEXT NOT NULL, outcome_status TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS outcome_labels (outcome_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL UNIQUE, matured_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS adaptive_evidence (evidence_id TEXT PRIMARY KEY, evidence_key TEXT NOT NULL UNIQUE, updated_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS adaptive_evidence_contributions (contribution_id TEXT PRIMARY KEY, evidence_key TEXT NOT NULL, outcome_id TEXT NOT NULL, contributed_at TEXT NOT NULL, UNIQUE(evidence_key, outcome_id));
CREATE TABLE IF NOT EXISTS worker_jobs (job_key TEXT PRIMARY KEY, job_type TEXT NOT NULL, target_time TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, last_updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS worker_status (worker_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL, last_updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reliability_outcomes (reliability_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, scope_key TEXT NOT NULL, horizon TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(reliability_id));
