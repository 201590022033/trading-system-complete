"""SQLite repository delegating existing entities to MarketIntelligenceStore."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from domain.intelligence.clustering import ClusteredEvent
from domain.registry.source import CanonicalSourcePolicy, CanonicalSourceRegistry
from evidence import EvidenceRecord
from market_intelligence.source_registry import SourceRegistry as LegacySourceRegistry
from market_intelligence.store import MarketIntelligenceStore

from .sql_models import dumps, loads
from shadow_learning import ObservationRecord, ShadowDecision, OutcomeLabel, AdaptiveEvidence, JobCheckpoint
from .jobs import DurableJobs


class SQLiteRepository(DurableJobs):
    backend = "sqlite"

    def __init__(self, path: str | Path = "market_intelligence.db") -> None:
        self.store = MarketIntelligenceStore(path)
        self.sources = CanonicalSourceRegistry(LegacySourceRegistry(self.store))

    def list_source_policies(self) -> list[CanonicalSourcePolicy]:
        return self.sources.list_policies()

    def get_source_policy(self, source_id: str) -> CanonicalSourcePolicy | None:
        return self.sources.get(source_id)

    def save_source_policy(self, policy: CanonicalSourcePolicy) -> CanonicalSourcePolicy:
        existing = self.sources.get(policy.source_id)
        if existing is None:
            return self.sources.register(policy)
        self.sources.legacy.store.upsert_source_policy({**policy.to_legacy().__dict__,
            "source_name": policy.display_name, "url": policy.endpoint, "weight": policy.manual_weight,
            "updated_at": datetime.now(timezone.utc).isoformat()})
        return policy

    def save_evidence(self, record: EvidenceRecord) -> None:
        self.store.save_evidence(record)

    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        return self.store.get_evidence(evidence_id)

    def save_clustered_event(self, event: ClusteredEvent) -> None:
        self.store._connection.execute(
            """INSERT OR REPLACE INTO clustered_events
            (event_id, policy_id, policy_version, first_observed_at, latest_observed_at,
             primary_headline, evidence_ids, source_ids, entity_references, macro_references,
             consensus_direction, aggregate_strength, duplicate_count)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event.event_id, event.cluster_policy_id, event.cluster_policy_version,
             event.first_observed_at, event.latest_observed_at, event.primary_headline,
             dumps(event.underlying_evidence_ids), dumps(event.source_ids),
             dumps(event.entity_references), dumps(event.macro_references),
             event.consensus_direction, event.aggregate_strength, event.duplicate_evidence_count))
        self.store._connection.commit()

    def list_clustered_events(self) -> list[ClusteredEvent]:
        rows = self.store._connection.execute("SELECT * FROM clustered_events ORDER BY first_observed_at, event_id").fetchall()
        return [ClusteredEvent(row["event_id"], row["policy_id"], row["policy_version"],
                               row["first_observed_at"], row["latest_observed_at"], row["primary_headline"],
                               tuple(loads(row["evidence_ids"], [])), tuple(loads(row["source_ids"], [])),
                               tuple(loads(row["entity_references"], [])), tuple(loads(row["macro_references"], [])),
                               row["consensus_direction"], row["aggregate_strength"], row["duplicate_count"])
                for row in rows]

    def append_audit_event(self, action: str, entity_type: str | None = None,
                           entity_id: str | None = None, after: dict | None = None) -> None:
        self.store.audit(action, entity_type, entity_id, after=after)

    def save_observation(self, record: ObservationRecord) -> None: self.store.save_observation(record)
    def save_shadow_decision(self, decision: ShadowDecision) -> None: self.store.save_shadow_decision(decision)
    def save_outcome(self, outcome: OutcomeLabel) -> None: self.store.save_outcome(outcome)
    def save_adaptive_evidence(self, evidence: AdaptiveEvidence) -> None: self.store.save_adaptive_evidence(evidence)
    def contribute_adaptive_evidence(self, evidence: AdaptiveEvidence, outcome_id: str) -> bool: return self.store.contribute_adaptive_evidence(evidence, outcome_id)
    def learning_status(self,now=None) -> dict:
        from .learning_status import learning_status
        return learning_status(self,now)
    def get_observation(self, observation_id: str) -> dict | None:
        row = self.store._connection.execute("SELECT payload FROM observations WHERE observation_id=?", (observation_id,)).fetchone()
        return loads(row[0], None) if row else None
    def get_shadow_decision(self, decision_id: str) -> dict | None:
        return self.store.get_shadow_decision(decision_id)
    def get_outcome(self, outcome_id: str) -> dict | None:
        row = self.store._connection.execute("SELECT payload FROM outcome_labels WHERE outcome_id=?", (outcome_id,)).fetchone()
        return loads(row[0], None) if row else None
    def get_job(self, job_key: str) -> dict | None:
        row = self.store._connection.execute("SELECT payload FROM worker_jobs WHERE job_key=?", (job_key,)).fetchone()
        return loads(row[0], None) if row else None
    def save_job(self, job: JobCheckpoint) -> None: self.store.save_job(job)
    def counts(self) -> dict[str, int]: return self.store.counts()
    def save_reliability_outcome(self, record: dict) -> None:
        self.store._connection.execute("INSERT OR IGNORE INTO reliability_outcomes VALUES (?, ?, ?, ?, ?)", (record["reliability_id"], record["source_id"], record["scope_key"], record["horizon"], dumps(record)))
        self.store._connection.commit()
    def list_reliability_outcomes(self, source_id: str, scope_key: str, horizon: str) -> list[dict]:
        rows = self.store._connection.execute("SELECT payload FROM reliability_outcomes WHERE source_id=? AND scope_key=? AND horizon=?", (source_id, scope_key, horizon)).fetchall()
        return [loads(row[0], {}) for row in rows]

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self.store.transaction():
            yield

    def close(self) -> None:
        self.store.close()
