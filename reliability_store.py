"""Research-only source registry and reliability store.

This module records evidence outcomes for future adaptive learning. It never
changes production signal weights and rejects outcome timestamps that precede
the evidence observation time.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    source_name: str
    source_class: str
    authority_tier: int
    enabled: bool = True


@dataclass(frozen=True)
class ReliabilitySummary:
    source_id: str
    scope_key: str
    horizon: str
    samples: int
    wins: int
    losses: int
    flats: int
    hit_rate: float
    mean_aligned_return: float
    reliability: float


class SourceRegistry:
    """In-memory registry of source definitions, easy to serialize later."""

    def __init__(self, definitions: Optional[Iterable[SourceDefinition]] = None):
        self._sources: Dict[str, SourceDefinition] = {}
        for definition in definitions or ():
            self.register(definition)

    def register(self, definition: SourceDefinition) -> None:
        if not definition.source_id.strip():
            raise ValueError("source_id cannot be empty")
        if definition.authority_tier < 1 or definition.authority_tier > 4:
            raise ValueError("authority_tier must be between 1 and 4")
        self._sources[definition.source_id] = definition

    def get(self, source_id: str) -> Optional[SourceDefinition]:
        return self._sources.get(source_id)

    def enabled(self):
        return [source for source in self._sources.values() if source.enabled]


class ReliabilityStore:
    """SQLite-backed research store for source outcomes and summaries."""

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                source_class TEXT NOT NULL,
                authority_tier INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS evidence_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                horizon TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                evaluated_at TEXT NOT NULL,
                direction INTEGER NOT NULL,
                forward_return REAL NOT NULL,
                aligned_return REAL NOT NULL,
                outcome TEXT NOT NULL CHECK(outcome IN ('win', 'loss', 'flat')),
                UNIQUE(evidence_id, scope_key, horizon)
            );
            CREATE INDEX IF NOT EXISTS idx_outcomes_scope
                ON evidence_outcomes(source_id, scope_key, horizon);
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def register_source(self, source: SourceDefinition) -> None:
        self.connection.execute(
            """INSERT INTO sources(source_id, source_name, source_class, authority_tier, enabled)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(source_id) DO UPDATE SET
                 source_name=excluded.source_name,
                 source_class=excluded.source_class,
                 authority_tier=excluded.authority_tier,
                 enabled=excluded.enabled""",
            (source.source_id, source.source_name, source.source_class,
             source.authority_tier, int(source.enabled)),
        )
        self.connection.commit()

    @staticmethod
    def _iso(value: datetime | str) -> str:
        if isinstance(value, str):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    def record_outcome(
        self,
        *,
        evidence_id: str,
        source_id: str,
        scope_key: str,
        horizon: str,
        observed_at: datetime | str,
        evaluated_at: datetime | str,
        direction: int,
        forward_return: float,
    ) -> None:
        """Record one outcome, rejecting look-ahead timestamps."""
        observed = self._iso(observed_at)
        evaluated = self._iso(evaluated_at)
        if evaluated < observed:
            raise ValueError("evaluated_at cannot precede observed_at")
        if direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0 or 1")

        aligned = direction * float(forward_return)
        outcome = "win" if aligned > 0 else "loss" if aligned < 0 else "flat"
        self.connection.execute(
            """INSERT OR IGNORE INTO evidence_outcomes
               (evidence_id, source_id, scope_key, horizon, observed_at,
                evaluated_at, direction, forward_return, aligned_return, outcome)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (evidence_id, source_id, scope_key, horizon, observed, evaluated,
             direction, float(forward_return), aligned, outcome),
        )
        self.connection.commit()

    def summarize(self, source_id: str, scope_key: str = "global", horizon: str = "5d") -> ReliabilitySummary:
        row = self.connection.execute(
            """SELECT COUNT(*) AS samples,
                      SUM(outcome = 'win') AS wins,
                      SUM(outcome = 'loss') AS losses,
                      SUM(outcome = 'flat') AS flats,
                      AVG(aligned_return) AS mean_aligned
               FROM evidence_outcomes
               WHERE source_id = ? AND scope_key = ? AND horizon = ?""",
            (source_id, scope_key, horizon),
        ).fetchone()
        samples = int(row["samples"] or 0)
        wins = int(row["wins"] or 0)
        losses = int(row["losses"] or 0)
        flats = int(row["flats"] or 0)
        hit_rate = wins / samples if samples else 0.0
        mean_aligned = float(row["mean_aligned"] or 0.0)

        # Conservative shrinkage toward a 50% prior; n=20 gives half weight.
        prior_samples = 20
        reliability = ((wins + prior_samples * 0.5) / (samples + prior_samples)) if samples else 0.5
        return ReliabilitySummary(
            source_id=source_id,
            scope_key=scope_key,
            horizon=horizon,
            samples=samples,
            wins=wins,
            losses=losses,
            flats=flats,
            hit_rate=round(hit_rate, 6),
            mean_aligned_return=round(mean_aligned, 8),
            reliability=round(reliability, 6),
        )
