CREATE TABLE IF NOT EXISTS source_policies (
source_id TEXT PRIMARY KEY, source_name TEXT NOT NULL, source_class TEXT NOT NULL,
authority_tier INTEGER NOT NULL, access_mode TEXT NOT NULL, status TEXT NOT NULL,
url TEXT, enabled BOOLEAN NOT NULL DEFAULT FALSE, weight DOUBLE PRECISION DEFAULT 1.0,
minimum_poll_seconds INTEGER DEFAULT 300, notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS evidence_records (
evidence_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, source_name TEXT NOT NULL,
source_class TEXT NOT NULL, authority_tier INTEGER NOT NULL, headline TEXT, text TEXT,
url TEXT, observed_at TEXT, published_at TEXT, ingested_at TEXT NOT NULL, tickers JSONB,
assets JSONB, sectors JSONB, sentiment TEXT, score DOUBLE PRECISION, confidence DOUBLE PRECISION,
horizon TEXT, parser_version TEXT, metadata JSONB);
CREATE TABLE IF NOT EXISTS audit_log (
id BIGSERIAL PRIMARY KEY, occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), actor TEXT,
action TEXT NOT NULL, entity_type TEXT, entity_id TEXT, after_json JSONB);
CREATE TABLE IF NOT EXISTS clustered_events (
event_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, policy_version TEXT NOT NULL,
first_observed_at TEXT NOT NULL, latest_observed_at TEXT NOT NULL, primary_headline TEXT NOT NULL,
evidence_ids TEXT NOT NULL, source_ids TEXT NOT NULL, entity_references TEXT NOT NULL,
macro_references TEXT NOT NULL, consensus_direction INTEGER NOT NULL,
aggregate_strength DOUBLE PRECISION NOT NULL, duplicate_count INTEGER NOT NULL
)
;CREATE TABLE IF NOT EXISTS observations (observation_id TEXT PRIMARY KEY, instrument TEXT NOT NULL, observed_at TEXT NOT NULL, horizon TEXT NOT NULL, payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL, source_version TEXT NOT NULL, pipeline_version TEXT NOT NULL, UNIQUE(instrument, observed_at, horizon, source_version, pipeline_version));
CREATE TABLE IF NOT EXISTS shadow_decisions (decision_id TEXT PRIMARY KEY, observation_id TEXT UNIQUE NOT NULL, instrument TEXT NOT NULL, decided_at TIMESTAMPTZ NOT NULL, horizon TEXT NOT NULL, action TEXT NOT NULL, outcome_status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS outcome_labels (outcome_id TEXT PRIMARY KEY, decision_id TEXT UNIQUE NOT NULL, matured_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS adaptive_evidence (evidence_id TEXT PRIMARY KEY, evidence_key TEXT UNIQUE NOT NULL, updated_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS worker_jobs (job_key TEXT PRIMARY KEY, job_type TEXT NOT NULL, target_time TIMESTAMPTZ NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, last_updated TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS worker_status (worker_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload JSONB NOT NULL, last_updated TIMESTAMPTZ NOT NULL);CREATE TABLE IF NOT EXISTS adaptive_evidence_contributions (contribution_id TEXT PRIMARY KEY, evidence_key TEXT NOT NULL, outcome_id TEXT NOT NULL, contributed_at TIMESTAMPTZ NOT NULL, UNIQUE(evidence_key, outcome_id));CREATE TABLE IF NOT EXISTS reliability_outcomes (reliability_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, scope_key TEXT NOT NULL, horizon TEXT NOT NULL, payload JSONB NOT NULL, UNIQUE(reliability_id));
