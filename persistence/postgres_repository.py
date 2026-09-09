"""PostgreSQL-compatible adapter boundary.

No PostgreSQL driver is required for local M6 work. A DB-API connection or
connection factory may be injected for integration tests; otherwise the adapter
fails explicitly when used rather than pretending a live connection exists.
"""

from contextlib import contextmanager
import json
from typing import Any, Callable, Iterator

from domain.intelligence.clustering import ClusteredEvent
from domain.registry.source import CanonicalSourcePolicy, CanonicalSourceRegistry
from evidence import EvidenceRecord


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


class PostgresRepository:
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
        return self._connection

    def initialize_sql(self) -> str:
        return POSTGRES_SCHEMA

    def initialize(self) -> None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            for statement in POSTGRES_SCHEMA.split(";"):
                if statement.strip():
                    cursor.execute(statement)
        connection.commit()

    def save_source_policy(self, policy: CanonicalSourcePolicy) -> None:
        connection = self._require_connection()
        legacy = policy.to_legacy()
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO source_policies
                (source_id, source_name, source_class, authority_tier, access_mode, status, url, enabled, weight, minimum_poll_seconds, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (source_id) DO UPDATE SET source_name=EXCLUDED.source_name, enabled=EXCLUDED.enabled,
                weight=EXCLUDED.weight, notes=EXCLUDED.notes, updated_at=NOW()""",
                (policy.source_id, legacy.source_name, legacy.source_class, legacy.authority_tier,
                 legacy.access_mode, legacy.status, legacy.url, legacy.enabled, policy.manual_weight,
                 policy.minimum_poll_seconds, policy.notes))
        connection.commit()

    def get_source_policy(self, source_id: str) -> dict | None:
        connection = self._require_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT source_id, source_name, source_class, authority_tier, access_mode, status, url, enabled, weight, minimum_poll_seconds, notes FROM source_policies WHERE source_id=%s", (source_id,))
            row = cursor.fetchone()
        if not row:
            return None
        return dict(zip(("source_id", "source_name", "source_class", "authority_tier", "access_mode", "status", "url", "enabled", "weight", "minimum_poll_seconds", "notes"), row))

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
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
