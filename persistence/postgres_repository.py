"""PostgreSQL-compatible adapter boundary.

No PostgreSQL driver is required for local M6 work. A DB-API connection or
connection factory may be injected for integration tests; otherwise the adapter
fails explicitly when used rather than pretending a live connection exists.
"""

from contextlib import contextmanager
import json
import hashlib
from pathlib import Path
from typing import Any, Callable, Iterator

from domain.intelligence.clustering import ClusteredEvent
from domain.registry.source import CanonicalSourcePolicy, CanonicalSourceRegistry
from evidence import EvidenceRecord
from shadow_learning import ObservationRecord, ShadowDecision, OutcomeLabel, AdaptiveEvidence, JobCheckpoint
from persistence_transactions import OwnedConnection, atomic
from .jobs import DurableJobs


POSTGRES_SCHEMA = """CREATE TABLE IF NOT EXISTS source_policies (
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
)"""
POSTGRES_SCHEMA += """
;CREATE TABLE IF NOT EXISTS observations (observation_id TEXT PRIMARY KEY, instrument TEXT NOT NULL, observed_at TEXT NOT NULL, horizon TEXT NOT NULL, payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL, source_version TEXT NOT NULL, pipeline_version TEXT NOT NULL, UNIQUE(instrument, observed_at, horizon, source_version, pipeline_version));
CREATE TABLE IF NOT EXISTS shadow_decisions (decision_id TEXT PRIMARY KEY, observation_id TEXT UNIQUE NOT NULL, instrument TEXT NOT NULL, decided_at TIMESTAMPTZ NOT NULL, horizon TEXT NOT NULL, action TEXT NOT NULL, outcome_status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS outcome_labels (outcome_id TEXT PRIMARY KEY, decision_id TEXT UNIQUE NOT NULL, matured_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS adaptive_evidence (evidence_id TEXT PRIMARY KEY, evidence_key TEXT UNIQUE NOT NULL, updated_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS worker_jobs (job_key TEXT PRIMARY KEY, job_type TEXT NOT NULL, target_time TIMESTAMPTZ NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, last_updated TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS worker_status (worker_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload JSONB NOT NULL, last_updated TIMESTAMPTZ NOT NULL)"""
POSTGRES_SCHEMA += ";CREATE TABLE IF NOT EXISTS adaptive_evidence_contributions (contribution_id TEXT PRIMARY KEY, evidence_key TEXT NOT NULL, outcome_id TEXT NOT NULL, contributed_at TIMESTAMPTZ NOT NULL, UNIQUE(evidence_key, outcome_id))"
POSTGRES_SCHEMA += ";CREATE TABLE IF NOT EXISTS reliability_outcomes (reliability_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, scope_key TEXT NOT NULL, horizon TEXT NOT NULL, payload JSONB NOT NULL, UNIQUE(reliability_id))"


class PostgresRepository(DurableJobs):
    backend = "postgresql"

    def __init__(self, database_url: str, connection: Any = None,
                 connection_factory: Callable[[str], Any] | None = None) -> None:
        if not database_url.lower().startswith(("postgresql://", "postgres://")):
            raise ValueError("PostgresRepository requires a PostgreSQL DATABASE_URL")
        self.database_url = database_url
        self._connection = connection
        self._connection_factory = connection_factory

    @property
    def connected(self) -> bool:
        return self._connection is not None

    def _require_connection(self) -> Any:
        if self._connection is None and self._connection_factory is not None:
            self._connection = self._connection_factory(self.database_url)
        if self._connection is None:
            try:
                import psycopg
            except ImportError as exc:
                raise RuntimeError("psycopg is required for PostgreSQL integration") from exc
            self._connection = psycopg.connect(self.database_url)
        if not isinstance(self._connection, OwnedConnection):
            self._connection = OwnedConnection(self._connection)
        return self._connection

    def initialize_sql(self) -> str:
        return '\n'.join(path.read_text(encoding='utf-8') for path in self._migration_files())

    @staticmethod
    def _migration_files():
        return sorted((Path(__file__).parent/'migrations'/'postgres').glob('*.sql'))

    @property
    def store(self):
        if not hasattr(self,'_market_store'):
            from .postgres_store import market_store
            self._market_store=market_store(self)
        return self._market_store

    @property
    def sources(self):
        from market_intelligence.source_registry import SourceRegistry
        return CanonicalSourceRegistry(SourceRegistry(self.store))

    def list_source_policies(self):
        return self.sources.list_policies()

    def get_evidence(self,evidence_id):
        return self.store.get_evidence(evidence_id)

    def list_clustered_events(self):
        # The existing serializer operates only on store rows, not SQLite SQL.
        from .sqlite_repository import SQLiteRepository
        return SQLiteRepository.list_clustered_events(self)

    @atomic
    def initialize(self) -> None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(718492001)')
            cursor.execute('CREATE TABLE IF NOT EXISTS postgres_schema_migrations (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())')
            for path in self._migration_files():
                version=int(path.name.split('_')[0])
                sql=path.read_text(encoding='utf-8')
                checksum=hashlib.sha256(sql.encode('utf-8')).hexdigest()
                cursor.execute('SELECT checksum FROM postgres_schema_migrations WHERE version=%s',(version,))
                applied=cursor.fetchone()
                if applied:
                    if applied[0]!=checksum: raise ValueError('applied migration checksum mismatch')
                    continue
                for statement in sql.split(';'):
                    if statement.strip(): cursor.execute(statement)
                cursor.execute('INSERT INTO postgres_schema_migrations (version,checksum) VALUES (%s,%s)',(version,checksum))
            # NOT VALID preserves legacy rows but enforces all new writes.
            for name, table, column, parent, parent_column in (
                ("shadow_decision_observation_fk", "shadow_decisions", "observation_id", "observations", "observation_id"),
                ("shadow_outcome_decision_fk", "outcome_labels", "decision_id", "shadow_decisions", "decision_id"),
                ("shadow_contribution_outcome_fk", "adaptive_evidence_contributions", "outcome_id", "outcome_labels", "outcome_id"),
            ):
                cursor.execute("SELECT 1 FROM pg_constraint WHERE conname=%s AND conrelid=%s::regclass", (name, table))
                if cursor.fetchone() is None:
                    cursor.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {parent} ({parent_column}) NOT VALID")
        connection.commit()

    def _insert(self, table: str, conflict: str, columns: tuple[str, ...], values: tuple[Any, ...]) -> None:
        c = self._require_connection()
        names = ",".join(columns); marks = ",".join(["%s"] * len(columns))
        with c.cursor() as cur: cur.execute(f"INSERT INTO {table} ({names}) VALUES ({marks}) ON CONFLICT DO NOTHING", values)
        c.commit()

    @atomic
    def save_observation(self, record: ObservationRecord) -> None:
        record = ObservationRecord(**record.to_dict())
        self._insert("observations", "observation_id", ("observation_id","instrument","observed_at","horizon","payload","created_at","source_version","pipeline_version"), (record.observation_id,record.instrument,record.observed_at,record.horizon,json.dumps(record.to_dict()),record.created_at or record.observed_at,record.source_version,record.pipeline_version))
        with self._require_connection().cursor() as cur:
            cur.execute("SELECT payload FROM observations WHERE observation_id=%s OR (instrument=%s AND observed_at=%s AND horizon=%s AND source_version=%s AND pipeline_version=%s)",
                (record.observation_id,record.instrument,record.observed_at,record.horizon,record.source_version,record.pipeline_version))
            rows=cur.fetchall()
        self._assert_identical(rows,record.to_dict())

    @staticmethod
    def _assert_identical(rows, payload):
        if len(rows)!=1 or (json.loads(rows[0][0]) if isinstance(rows[0][0],str) else rows[0][0]) != payload:
            raise ValueError("conflicting immutable ledger record")

    @atomic
    def save_shadow_decision(self, decision: ShadowDecision) -> None:
        from shadow_learning_validation import validate_decision
        validate_decision(self, decision)
        self._insert("shadow_decisions", "decision_id", ("decision_id","observation_id","instrument","decided_at","horizon","action","outcome_status","payload"), (decision.decision_id,decision.observation_id,decision.instrument,decision.decided_at,decision.horizon,decision.action,decision.outcome_status,json.dumps(decision.to_dict())))
        with self._require_connection().cursor() as cur:
            cur.execute("SELECT payload FROM shadow_decisions WHERE decision_id=%s OR observation_id=%s",(decision.decision_id,decision.observation_id))
            self._assert_identical(cur.fetchall(),decision.to_dict())
    @atomic
    def save_outcome(self, outcome: OutcomeLabel) -> None:
        from shadow_learning_validation import validate_outcome
        validate_outcome(self, outcome)
        self._insert("outcome_labels", "outcome_id", ("outcome_id","decision_id","matured_at","payload"), (outcome.outcome_id,outcome.decision_id,outcome.matured_at,json.dumps(outcome.to_dict())))
        c = self._require_connection()
        with c.cursor() as cur:
            cur.execute("SELECT payload FROM outcome_labels WHERE outcome_id=%s OR decision_id=%s",(outcome.outcome_id,outcome.decision_id))
            self._assert_identical(cur.fetchall(),outcome.to_dict())
            status = "OUTCOME_DATA_UNAVAILABLE" if outcome.label == "OUTCOME_DATA_UNAVAILABLE" else "LABELLED"
            cur.execute("UPDATE shadow_decisions SET outcome_status = %s WHERE decision_id = %s", (status, outcome.decision_id))
        c.commit()
    def save_adaptive_evidence(self, evidence: AdaptiveEvidence) -> None:
        if not getattr(self,"_contributing",False):
            raise ValueError("adaptive aggregates require a validated contribution")
        with self._require_connection().cursor() as cur:
            cur.execute("UPDATE adaptive_evidence SET updated_at=%s,payload=%s WHERE evidence_key=%s",(evidence.updated_at,json.dumps(evidence.to_dict()),self._evidence_key(evidence)))

    def _evidence_key(self, evidence):
        from shadow_learning import evidence_key
        return evidence_key(evidence,lambda key:self._read_payload("adaptive_evidence","evidence_key",key))

    @atomic
    def save_job(self, job: JobCheckpoint) -> None:
        with self._require_connection().cursor() as cur:
            cur.execute("INSERT INTO worker_jobs VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(job_key) DO UPDATE SET status=excluded.status,payload=excluded.payload,last_updated=excluded.last_updated",
                (job.job_key,job.job_type,job.target_time,job.status,json.dumps(job.to_dict()),job.last_updated or job.target_time))

    @atomic
    def contribute_adaptive_evidence(self, evidence: AdaptiveEvidence, outcome_id: str) -> bool:
        from shadow_learning_validation import validate_evidence
        validate_evidence(self, evidence, outcome_id)
        from shadow_learning import stable_id
        c = self._require_connection(); key = self._evidence_key(evidence)
        with c.cursor() as cur:
            cur.execute("INSERT INTO adaptive_evidence_contributions VALUES (%s,%s,%s,%s) ON CONFLICT (evidence_key,outcome_id) DO NOTHING", (stable_id("contribution",key,outcome_id), key, outcome_id, evidence.updated_at))
            inserted = cur.rowcount > 0
            if not inserted: return False
            from dataclasses import replace
            empty=replace(evidence,sample_count=0,wins=0,losses=0,mean_net_return=0.0)
            cur.execute("INSERT INTO adaptive_evidence VALUES (%s,%s,%s,%s) ON CONFLICT(evidence_key) DO NOTHING",(empty.evidence_id,key,empty.updated_at,json.dumps(empty.to_dict())))
            cur.execute("SELECT payload FROM adaptive_evidence WHERE evidence_key=%s FOR UPDATE",(key,))
            row=cur.fetchone()[0]; prior=json.loads(row) if isinstance(row,str) else row
            count=prior['sample_count']+1
            merged=AdaptiveEvidence(**{**prior,'sample_count':count,'wins':prior['wins']+evidence.wins,
                'losses':prior['losses']+evidence.losses,'mean_net_return':(prior['mean_net_return']*(count-1)+evidence.mean_net_return)/count,
                'updated_at':evidence.updated_at})
        self._contributing=True
        try: self.save_adaptive_evidence(merged)
        finally: self._contributing=False
        return True

    def learning_status(self, now=None) -> dict:
        """Return persisted status using database timestamps only."""
        from .learning_status import learning_status
        return learning_status(self,now)

    def _read_payload(self, table: str, key_column: str, value: str) -> dict | None:
        c = self._require_connection()
        with c.cursor() as cur:
            cur.execute(f"SELECT payload FROM {table} WHERE {key_column} = %s", (value,))
            row = cur.fetchone()
        if not row: return None
        payload = row[0]
        return json.loads(payload) if isinstance(payload, str) else payload

    def get_observation(self, observation_id: str) -> dict | None:
        return self._read_payload("observations", "observation_id", observation_id)
    def get_shadow_decision(self, decision_id: str) -> dict | None:
        c = self._require_connection()
        with c.cursor() as cur:
            cur.execute("SELECT payload, outcome_status FROM shadow_decisions WHERE decision_id = %s", (decision_id,)); row = cur.fetchone()
        if not row: return None
        result = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        result["outcome_status"] = row[1]
        return result
    def get_outcome(self, outcome_id: str) -> dict | None:
        return self._read_payload("outcome_labels", "outcome_id", outcome_id)
    def get_job(self, job_key: str) -> dict | None:
        return self._read_payload("worker_jobs", "job_key", job_key)
    def save_reliability_outcome(self, record: dict) -> None:
        self._insert("reliability_outcomes", "reliability_id", ("reliability_id","source_id","scope_key","horizon","payload"), (record["reliability_id"],record["source_id"],record["scope_key"],record["horizon"],json.dumps(record)))
    def list_reliability_outcomes(self, source_id: str, scope_key: str, horizon: str) -> list[dict]:
        c = self._require_connection()
        with c.cursor() as cur:
            cur.execute("SELECT payload FROM reliability_outcomes WHERE source_id=%s AND scope_key=%s AND horizon=%s", (source_id, scope_key, horizon)); rows = cur.fetchall()
        return [json.loads(row[0]) if isinstance(row[0], str) else row[0] for row in rows]

    def save_source_policy(self, policy: CanonicalSourcePolicy) -> None:
        from .sqlite_repository import SQLiteRepository
        return SQLiteRepository.save_source_policy(self,policy)

    def get_source_policy(self, source_id: str) -> dict | None:
        return self.sources.get(source_id)

    def save_evidence(self, record: EvidenceRecord) -> None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO evidence_records
                (evidence_id, source_id, source_name, source_class, authority_tier, headline, text, url, observed_at, published_at, ingested_at, tickers, assets, sectors, sentiment, score, confidence, horizon, parser_version, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb)
                ON CONFLICT (evidence_id) DO NOTHING""",
                (record.evidence_id, record.source_id, record.source_name, record.source_class, record.authority_tier,
                 record.headline, record.text, record.url, record.observed_at, record.published_at, record.ingested_at,
                 json.dumps(record.tickers), json.dumps(record.assets), json.dumps(record.sectors), record.sentiment,
                 record.score, record.confidence, record.horizon, record.parser_version, json.dumps(record.metadata)))
        connection.commit()

    def evidence_exists(self, evidence_id: str) -> bool:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM evidence_records WHERE evidence_id=%s", (evidence_id,))
            return cursor.fetchone() is not None

    def evidence_ingested_at(self, evidence_id: str) -> str | None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT ingested_at FROM evidence_records WHERE evidence_id=%s", (evidence_id,))
            row = cursor.fetchone()
        return row[0] if row else None

    def save_clustered_event(self, event: ClusteredEvent) -> None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO clustered_events
                (event_id, policy_id, policy_version, first_observed_at, latest_observed_at, primary_headline, evidence_ids, source_ids, entity_references, macro_references, consensus_direction, aggregate_strength, duplicate_count)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_id) DO NOTHING""",
                (event.event_id, event.cluster_policy_id, event.cluster_policy_version, event.first_observed_at,
                 event.latest_observed_at, event.primary_headline, json.dumps(event.underlying_evidence_ids),
                 json.dumps(event.source_ids), json.dumps(event.entity_references), json.dumps(event.macro_references),
                 event.consensus_direction, event.aggregate_strength, event.duplicate_evidence_count))
        connection.commit()

    def clustered_event_exists(self, event_id: str) -> bool:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM clustered_events WHERE event_id=%s", (event_id,))
            return cursor.fetchone() is not None

    def append_audit_event(self, action: str, entity_type: str, entity_id: str, after: dict) -> None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO audit_log (action, entity_type, entity_id, after_json) VALUES (%s,%s,%s,%s::jsonb)", (action, entity_type, entity_id, json.dumps(after)))
        connection.commit()

    def audit_exists(self, action: str, entity_id: str) -> bool:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM audit_log WHERE action=%s AND entity_id=%s", (action, entity_id))
            return cursor.fetchone() is not None

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        connection = self._require_connection()
        with connection.transaction():
            yield connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
