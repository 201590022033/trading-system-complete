-- Additive guards: existing rows are preserved. Legacy invalid rows remain
-- quarantined by repository validation and are never eligible for evidence.
-- An early schema_version=4 installation predates this contribution ledger.
CREATE TABLE IF NOT EXISTS adaptive_evidence_contributions (
    contribution_id TEXT PRIMARY KEY, evidence_key TEXT NOT NULL,
    outcome_id TEXT NOT NULL, contributed_at TEXT NOT NULL,
    UNIQUE(evidence_key, outcome_id));
CREATE TRIGGER IF NOT EXISTS shadow_observation_parent
BEFORE INSERT ON shadow_decisions
WHEN NOT EXISTS (SELECT 1 FROM observations WHERE observation_id=NEW.observation_id
    AND instrument=NEW.instrument AND horizon=NEW.horizon AND observed_at=NEW.decided_at)
BEGIN
    SELECT RAISE(ABORT, 'shadow decision requires matching observation');
END;
CREATE TRIGGER IF NOT EXISTS shadow_outcome_parent
BEFORE INSERT ON outcome_labels
WHEN NOT EXISTS (SELECT 1 FROM shadow_decisions WHERE decision_id=NEW.decision_id
    AND decided_at < NEW.matured_at)
BEGIN
    SELECT RAISE(ABORT, 'outcome requires earlier decision');
END;
CREATE TRIGGER IF NOT EXISTS shadow_contribution_parent
BEFORE INSERT ON adaptive_evidence_contributions
WHEN NOT EXISTS (SELECT 1 FROM outcome_labels WHERE outcome_id=NEW.outcome_id)
BEGIN
    SELECT RAISE(ABORT, 'contribution requires outcome');
END;
