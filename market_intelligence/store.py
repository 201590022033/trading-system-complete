"""SQLite-backed store for market intelligence, source config, documents and audit.

The store is append-only for evidence, narratives, ticker selections and audit
records. Source policies are mutable configuration. Documents are deduplicated by
content hash so the same PDF is never analysed twice.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from evidence import EvidenceRecord

from .schemas import (InstrumentCandidate, MarketNarrative, MarketTheme, TickerSelection,
                      MarketIntelligenceSnapshot, ProvenanceEdge, MarketDocumentAnalysis,
                      DocumentFact)
from shadow_learning import (ObservationRecord, ShadowDecision, OutcomeLabel,
                             AdaptiveEvidence, JobCheckpoint, LearningStatus)
from persistence_transactions import OwnedConnection, atomic


DEFAULT_DB_PATH = "market_intelligence.db"
SCHEMA_VERSION_TABLE = "schema_version"


class MarketIntelligenceStore:
    """Persistent store for market-intelligence state."""

    def __init__(self, path: str | Path = DEFAULT_DB_PATH) -> None:
        self.path = str(path)
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_connection()
        self._run_migrations()

    def _ensure_connection(self) -> None:
        if self._connection is None:
            self._connection = sqlite3.connect(self.path)
            self._connection.row_factory = sqlite3.Row
            self._connection = OwnedConnection(self._connection)

    def transaction(self):
        return self._connection.transaction()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ------------------------------------------------------------------
    # Persistent shadow-learning ledgers
    # ------------------------------------------------------------------
    @atomic
    def save_observation(self, record: ObservationRecord) -> None:
        record = ObservationRecord(**record.to_dict())
        payload = json.dumps(record.to_dict(), sort_keys=True)
        self._connection.execute("INSERT OR IGNORE INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record.observation_id, record.instrument, record.observed_at, record.horizon, payload,
             record.created_at or record.observed_at, record.source_version, record.pipeline_version))
        row = self._connection.execute("SELECT payload FROM observations WHERE observation_id=? OR (instrument=? AND observed_at=? AND horizon=? AND source_version=? AND pipeline_version=?)",
            (record.observation_id,record.instrument,record.observed_at,record.horizon,record.source_version,record.pipeline_version)).fetchall()
        if len(row) != 1 or json.loads(row[0][0]) != record.to_dict():
            raise ValueError("conflicting immutable observation")
        self._connection.commit()

    @atomic
    def save_shadow_decision(self, decision: ShadowDecision) -> None:
        from shadow_learning_validation import validate_decision
        validate_decision(self, decision)
        self._connection.execute("INSERT OR IGNORE INTO shadow_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (decision.decision_id, decision.observation_id, decision.instrument, decision.decided_at,
             decision.horizon, decision.action, decision.outcome_status, json.dumps(decision.to_dict(), sort_keys=True)))
        row = self._connection.execute("SELECT payload FROM shadow_decisions WHERE decision_id=? OR observation_id=?", (decision.decision_id,decision.observation_id)).fetchall()
        if len(row) != 1 or json.loads(row[0][0]) != decision.to_dict():
            raise ValueError("conflicting immutable decision")
        self._connection.commit()

    @atomic
    def save_outcome(self, outcome: OutcomeLabel) -> None:
        from shadow_learning_validation import validate_outcome
        validate_outcome(self, outcome)
        self._connection.execute("INSERT OR IGNORE INTO outcome_labels VALUES (?, ?, ?, ?)",
            (outcome.outcome_id, outcome.decision_id, outcome.matured_at, json.dumps(outcome.to_dict(), sort_keys=True)))
        row = self._connection.execute("SELECT payload FROM outcome_labels WHERE outcome_id=? OR decision_id=?", (outcome.outcome_id,outcome.decision_id)).fetchall()
        if len(row) != 1 or json.loads(row[0][0]) != outcome.to_dict():
            raise ValueError("conflicting immutable outcome")
        status = "OUTCOME_DATA_UNAVAILABLE" if outcome.label == "OUTCOME_DATA_UNAVAILABLE" else "LABELLED"
        self._connection.execute("UPDATE shadow_decisions SET outcome_status = ? WHERE decision_id = ?", (status, outcome.decision_id))
        self._connection.commit()

    def save_adaptive_evidence(self, evidence: AdaptiveEvidence) -> None:
        if not getattr(self, "_contributing", False):
            raise ValueError("adaptive aggregates require a validated contribution")
        self._connection.execute("INSERT INTO adaptive_evidence VALUES (?, ?, ?, ?) ON CONFLICT(evidence_key) DO UPDATE SET updated_at=excluded.updated_at, payload=excluded.payload",
            (evidence.evidence_id, self._evidence_key(evidence), evidence.updated_at, json.dumps(evidence.to_dict(), sort_keys=True)))
        self._connection.commit()

    @atomic
    def contribute_adaptive_evidence(self, evidence: AdaptiveEvidence, outcome_id: str) -> bool:
        """Atomically register one outcome's contribution to one shadow cell."""
        from shadow_learning_validation import validate_evidence
        validate_evidence(self, evidence, outcome_id)
        from shadow_learning import stable_id
        key = self._evidence_key(evidence)
        cur = self._connection.execute("INSERT OR IGNORE INTO adaptive_evidence_contributions VALUES (?, ?, ?, ?)",
            (stable_id("contribution",key,outcome_id), key, outcome_id, evidence.updated_at))
        if cur.rowcount == 0:
            return False
        key_row = self._connection.execute("SELECT payload FROM adaptive_evidence WHERE evidence_key = ?", (key,)).fetchone()
        if key_row:
            prior = json.loads(key_row[0])
            total = int(prior.get("sample_count", 0)) + 1
            prior["sample_count"] = total
            prior["wins"] = int(prior.get("wins", 0)) + evidence.wins
            prior["losses"] = int(prior.get("losses", 0)) + evidence.losses
            prior["mean_net_return"] = ((prior.get("mean_net_return") or 0.0) * (total - 1) + (evidence.mean_net_return or 0.0)) / total
            evidence = AdaptiveEvidence(**{**prior, "updated_at": evidence.updated_at})
        self._contributing = True
        try:
            self.save_adaptive_evidence(evidence)
        finally:
            self._contributing = False
        return True

    def _evidence_key(self, evidence):
        from shadow_learning import evidence_key
        return evidence_key(evidence, lambda key: self._ledger_payload("adaptive_evidence","evidence_key",key))

    def _ledger_payload(self, table, key, value):
        row = self._connection.execute(f"SELECT payload FROM {table} WHERE {key}=?", (value,)).fetchone()
        return json.loads(row[0]) if row else None

    def get_observation(self, observation_id):
        return self._ledger_payload("observations", "observation_id", observation_id)

    def get_shadow_decision(self, decision_id):
        row = self._connection.execute("SELECT payload, outcome_status FROM shadow_decisions WHERE decision_id=?", (decision_id,)).fetchone()
        return {**json.loads(row[0]), "outcome_status": row[1]} if row else None

    def get_outcome(self, outcome_id):
        return self._ledger_payload("outcome_labels", "outcome_id", outcome_id)

    def learning_status(self) -> dict:
        counts = self.counts()
        now = datetime.now(timezone.utc)
        result = {"observations": {}, "shadow_decisions": {}, "labelled_outcomes": {}, "adaptive_updates": {},
                  "pending_outcomes": counts["pending_outcomes"], "latest_timestamps": {},
                  "database_backend": "sqlite", "database_state": "AVAILABLE", "worker_status": {"status": "UNKNOWN"}}
        for label, table, column in (("observations", "observations", "observed_at"), ("shadow_decisions", "shadow_decisions", "decided_at"), ("labelled_outcomes", "outcome_labels", "matured_at"), ("adaptive_updates", "adaptive_evidence", "updated_at")):
            for name, seconds in (("24h", 86400), ("3d", 259200), ("7d", 604800)):
                cutoff = (now - timedelta(seconds=seconds)).isoformat()
                result[label][name] = self._connection.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} >= ?", (cutoff,)).fetchone()[0]
            result["latest_timestamps"][label] = self._connection.execute(f"SELECT MAX({column}) FROM {table}").fetchone()[0]
        return result

    def save_job(self, job: JobCheckpoint) -> None:
        self._connection.execute("INSERT INTO worker_jobs VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(job_key) DO UPDATE SET status=excluded.status, payload=excluded.payload, last_updated=excluded.last_updated",
            (job.job_key, job.job_type, job.target_time, job.status, json.dumps(job.to_dict(), sort_keys=True), job.last_updated or job.target_time))
        self._connection.commit()

    def counts(self) -> dict[str, int]:
        q = lambda table: self._connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return {"observations": q("observations"), "shadow_decisions": q("shadow_decisions"), "labelled_outcomes": q("outcome_labels"), "adaptive_updates": q("adaptive_evidence"), "pending_outcomes": self._connection.execute("SELECT COUNT(*) FROM shadow_decisions WHERE outcome_status='PENDING_OUTCOME'").fetchone()[0]}

    def _run_migrations(self) -> None:
        """Run SQL migration files in order and track schema_version."""
        self._connection.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA_VERSION_TABLE} (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

        migrations_dir = Path(__file__).resolve().parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))
        for migration_path in migration_files:
            version = int(migration_path.stem.split("_")[0])
            already_applied = self._connection.execute(
                f"SELECT 1 FROM {SCHEMA_VERSION_TABLE} WHERE version = ?", (version,)
            ).fetchone()
            if already_applied:
                continue
            sql = migration_path.read_text(encoding="utf-8")
            self._connection.executescript(sql)
            self._connection.execute(
                f"INSERT INTO {SCHEMA_VERSION_TABLE}(version, applied_at) VALUES (?, datetime('now'))",
                (version,),
            )
            self._connection.commit()

    # ------------------------------------------------------------------
    # Source policies
    # ------------------------------------------------------------------
    def list_source_policies(self) -> List[Dict[str, Any]]:
        cursor = self._connection.execute(
            "SELECT * FROM source_policies ORDER BY source_class, source_name"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_source_policy(self, source_id: str) -> Optional[Dict[str, Any]]:
        row = self._connection.execute(
            "SELECT * FROM source_policies WHERE source_id = ?", (source_id,)
        ).fetchone()
        return dict(row) if row else None

    def upsert_source_policy(self, policy: Dict[str, Any]) -> None:
        fields = {
            "source_id",
            "source_name",
            "source_class",
            "authority_tier",
            "access_mode",
            "status",
            "region",
            "market_relevance",
            "url",
            "enabled",
            "weight",
            "minimum_poll_seconds",
            "notes",
            "created_at",
            "updated_at",
        }
        data = {k: v for k, v in policy.items() if k in fields}
        for required in ("source_id", "source_name", "source_class", "authority_tier", "access_mode", "status"):
            if required not in data:
                raise ValueError(f"source policy missing {required}")
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "source_id")
        sql = (
            f"INSERT INTO source_policies ({columns}) VALUES ({placeholders}) "
            f"ON CONFLICT(source_id) DO UPDATE SET {updates}"
        )
        self._connection.execute(sql, tuple(data.values()))
        self._connection.commit()

    def delete_source_policy(self, source_id: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM source_policies WHERE source_id = ?", (source_id,)
        )
        self._connection.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Evidence records
    # ------------------------------------------------------------------
    def save_evidence(self, record: EvidenceRecord) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO evidence_records (
                evidence_id, source_id, source_name, source_class, authority_tier,
                headline, text, url, observed_at, published_at, ingested_at,
                tickers, assets, sectors, sentiment, score, confidence, horizon,
                parser_version, metadata, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.evidence_id,
                record.source_id,
                record.source_name,
                record.source_class,
                record.authority_tier,
                record.headline,
                record.text,
                record.url,
                record.observed_at,
                record.published_at,
                record.ingested_at,
                json.dumps(record.tickers),
                json.dumps(record.assets),
                json.dumps(record.sectors),
                record.sentiment,
                record.score,
                record.confidence,
                record.horizon,
                record.parser_version,
                json.dumps(record.metadata),
                record.metadata.get("content_hash") if record.metadata else None,
            ),
        )
        self._connection.commit()

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        row = self._connection.execute(
            "SELECT * FROM evidence_records WHERE evidence_id = ?", (evidence_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_evidence(dict(row))

    def list_evidence(
        self,
        source_id: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 1000,
    ) -> List[EvidenceRecord]:
        sql = "SELECT * FROM evidence_records WHERE 1=1"
        params: List[Any] = []
        if source_id:
            sql += " AND source_id = ?"
            params.append(source_id)
        if since:
            sql += " AND ingested_at > ?"
            params.append(since)
        sql += " ORDER BY ingested_at DESC LIMIT ?"
        params.append(limit)
        rows = self._connection.execute(sql, params).fetchall()
        return [self._row_to_evidence(dict(row)) for row in rows]

    @staticmethod
    def _row_to_evidence(row: Dict[str, Any]) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=row["evidence_id"],
            source_id=row["source_id"],
            source_name=row["source_name"],
            source_class=row["source_class"],
            authority_tier=row["authority_tier"],
            headline=row["headline"],
            text=row["text"],
            url=row["url"],
            observed_at=row["observed_at"],
            published_at=row["published_at"],
            ingested_at=row["ingested_at"],
            tickers=json.loads(row["tickers"] or "[]"),
            assets=json.loads(row["assets"] or "[]"),
            sectors=json.loads(row["sectors"] or "[]"),
            sentiment=row["sentiment"],
            score=row["score"],
            confidence=row["confidence"],
            horizon=row["horizon"],
            parser_version=row["parser_version"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    # ------------------------------------------------------------------
    # Market narratives
    # ------------------------------------------------------------------
    def save_narrative(self, narrative: MarketNarrative) -> None:
        self._connection.execute(
            """
            INSERT INTO market_narratives (
                narrative_id, generated_at, model, provider, schema_version,
                enabled_sources, summary, themes, candidates, selected_tickers,
                top_opportunities, prompt_version, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                narrative.narrative_id,
                narrative.generated_at,
                narrative.model,
                narrative.provider,
                narrative.schema_version,
                json.dumps(narrative.enabled_sources),
                narrative.summary,
                json.dumps([asdict(t) for t in narrative.themes]),
                json.dumps([asdict(c) for c in narrative.candidates]),
                json.dumps([]),
                json.dumps([]),
                narrative.metadata.get("prompt_version"),
                json.dumps(narrative.metadata),
            ),
        )
        self._connection.commit()

    def latest_narrative(self) -> Optional[MarketNarrative]:
        row = self._connection.execute(
            "SELECT * FROM market_narratives ORDER BY generated_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return self._row_to_narrative(dict(row))

    @staticmethod
    def _row_to_narrative(row: Dict[str, Any]) -> MarketNarrative:
        return MarketNarrative(
            narrative_id=row["narrative_id"],
            generated_at=row["generated_at"],
            model=row["model"],
            provider=row["provider"],
            schema_version=row["schema_version"],
            summary=row["summary"],
            enabled_sources=json.loads(row["enabled_sources"] or "[]"),
            themes=[MarketTheme(**t) for t in json.loads(row["themes"] or "[]")],
            candidates=[InstrumentCandidate(**c) for c in json.loads(row["candidates"] or "[]")],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    # ------------------------------------------------------------------
    # Ticker selections
    # ------------------------------------------------------------------
    def save_ticker_selection(self, selection: TickerSelection) -> None:
        self._connection.execute(
            """
            INSERT INTO ticker_selections (
                instrument_id, display_symbol, pinned, reason, theme, confidence,
                source_evidence_ids, selected_at, review_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                selection.instrument_id,
                selection.display_symbol,
                int(selection.pinned),
                selection.reason,
                selection.theme,
                selection.confidence,
                json.dumps(selection.source_evidence_ids),
                selection.selected_at,
                selection.review_at,
                "active",
            ),
        )
        self._connection.commit()

    def active_ticker_selections(self) -> List[TickerSelection]:
        rows = self._connection.execute(
            "SELECT * FROM ticker_selections WHERE status = 'active' ORDER BY selected_at DESC"
        ).fetchall()
        return [self._row_to_ticker_selection(dict(row)) for row in rows]

    @staticmethod
    def _row_to_ticker_selection(row: Dict[str, Any]) -> TickerSelection:
        return TickerSelection(
            instrument_id=row["instrument_id"],
            display_symbol=row["display_symbol"],
            pinned=bool(row["pinned"]),
            reason=row["reason"],
            theme=row["theme"],
            confidence=row["confidence"],
            source_evidence_ids=json.loads(row["source_evidence_ids"] or "[]"),
            selected_at=row["selected_at"],
            review_at=row["review_at"],
        )

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------
    def audit(
        self,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        actor: str = "system",
        correlation_id: Optional[str] = None,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO audit_log (occurred_at, actor, action, entity_type, entity_id,
                                   before_json, after_json, correlation_id)
            VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                actor,
                action,
                entity_type,
                entity_id,
                json.dumps(before) if before else None,
                json.dumps(after) if after else None,
                correlation_id,
            ),
        )
        self._connection.commit()

    def save_provenance_edge(self, edge: ProvenanceEdge) -> None:
        self._connection.execute(
            """INSERT OR IGNORE INTO provenance_edges
            (provenance_id,snapshot_id,from_type,from_id,relationship_type,to_type,to_id,confidence,reason,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (edge.provenance_id, edge.snapshot_id, edge.from_type, edge.from_id,
             edge.relationship_type, edge.to_type, edge.to_id, edge.confidence,
             edge.reason, edge.created_at))
        self._connection.commit()

    def provenance_for(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT * FROM provenance_edges WHERE (from_type=? AND from_id=?) OR (to_type=? AND to_id=?) ORDER BY created_at",
            (entity_type, entity_id, entity_type, entity_id)).fetchall()
        return [dict(row) for row in rows]

    def save_analysis(self, analysis: MarketDocumentAnalysis) -> None:
        self._connection.execute(
            """INSERT INTO document_analyses
            (analysis_id,document_id,provider,model,schema_version,prompt_version,content_hash,analysed_at,facts,themes,candidates,uncertainties,contradictions,usage)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (analysis.analysis_id, analysis.document_id, analysis.provider, analysis.model,
             analysis.schema_version, analysis.prompt_version, analysis.content_hash,
             analysis.analysed_at, json.dumps([asdict(x) for x in analysis.facts]),
             json.dumps([asdict(x) if hasattr(x, "__dataclass_fields__") else x for x in analysis.themes]),
             json.dumps([asdict(x) if hasattr(x, "__dataclass_fields__") else x for x in analysis.candidates]),
             json.dumps(analysis.uncertainties), json.dumps(analysis.contradictions), json.dumps(analysis.usage)))
        self._connection.commit()

    def get_analysis(self, analysis_id: str):
        row=self._connection.execute("SELECT * FROM document_analyses WHERE analysis_id=?",(analysis_id,)).fetchone()
        if not row: return None
        data=dict(row)
        return MarketDocumentAnalysis(data["analysis_id"],data["document_id"],data["provider"],data["model"],data["schema_version"],data["prompt_version"],data["content_hash"],data["analysed_at"],
            [DocumentFact(**x) for x in json.loads(data["facts"])],json.loads(data["themes"]),json.loads(data["candidates"]),json.loads(data["uncertainties"]),json.loads(data["contradictions"]),json.loads(data["usage"]))

    def cached_analysis(self, document_id, content_hash, provider, model, schema_version, prompt_version):
        row=self._connection.execute("SELECT analysis_id FROM document_analyses WHERE document_id=? AND content_hash=? AND provider=? AND model=? AND schema_version=? AND prompt_version=?",(document_id,content_hash,provider,model,schema_version,prompt_version)).fetchone()
        return self.get_analysis(row["analysis_id"]) if row else None

    def save_snapshot(self, snapshot: MarketIntelligenceSnapshot) -> None:
        self._connection.execute(
            """INSERT INTO intelligence_snapshots
            (snapshot_id,generated_at,schema_version,enabled_sources,document_hashes,themes,candidates,selections,provider_metadata,metadata)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (snapshot.snapshot_id, snapshot.generated_at, snapshot.schema_version,
             json.dumps(snapshot.enabled_sources), json.dumps(snapshot.document_hashes),
             json.dumps([asdict(x) for x in snapshot.themes]), json.dumps([asdict(x) for x in snapshot.candidates]),
             json.dumps([asdict(x) for x in snapshot.selections]), json.dumps(snapshot.provider_metadata),
             json.dumps(snapshot.metadata)))
        self._connection.commit()

    def get_snapshot(self, snapshot_id: str):
        row=self._connection.execute("SELECT * FROM intelligence_snapshots WHERE snapshot_id=?",(snapshot_id,)).fetchone()
        if not row:return None
        data=dict(row)
        return {"snapshot_id":data["snapshot_id"],"generated_at":data["generated_at"],"schema_version":data["schema_version"],
                "enabled_sources":json.loads(data["enabled_sources"]),"document_hashes":json.loads(data["document_hashes"]),
                "themes":json.loads(data["themes"]),"candidates":json.loads(data["candidates"]),"selections":json.loads(data["selections"]),
                "provider_metadata":json.loads(data["provider_metadata"]),"metadata":json.loads(data["metadata"])}
