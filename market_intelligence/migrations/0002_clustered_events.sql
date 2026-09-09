CREATE TABLE IF NOT EXISTS clustered_events (
    event_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    first_observed_at TEXT NOT NULL,
    latest_observed_at TEXT NOT NULL,
    primary_headline TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    source_ids TEXT NOT NULL,
    entity_references TEXT NOT NULL,
    macro_references TEXT NOT NULL,
    consensus_direction INTEGER NOT NULL,
    aggregate_strength REAL NOT NULL,
    duplicate_count INTEGER NOT NULL
);
