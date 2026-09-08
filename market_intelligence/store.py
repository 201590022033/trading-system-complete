"""SQLite-backed store for market intelligence, source config, documents and audit.

The store is append-only for evidence, narratives, ticker selections and audit
records. Source policies are mutable configuration. Documents are deduplicated by
content hash so the same PDF is never analysed twice.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from evidence import EvidenceRecord

from .schemas import InstrumentCandidate, MarketNarrative, MarketTheme, TickerSelection


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

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

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
