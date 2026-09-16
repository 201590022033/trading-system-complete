import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from persistence.postgres_repository import PostgresRepository
from shadow_learning import ObservationRecord, ShadowDecision, OutcomeLabel, AdaptiveEvidence, JobCheckpoint
from reliability_store import runtime_repository_reliability
from shadow_test_fixtures import decision as ShadowDecision, complete_label
from dataclasses import replace


class SQLiteDBAPIForPostgres:
    """Small DB-API double: PostgreSQL repository SQL executes against isolated SQLite."""
    def __init__(self, path): self.db = sqlite3.connect(path)
    def cursor(self): return _Cursor(self.db.cursor())
    def commit(self): self.db.commit()
    def rollback(self): self.db.rollback()
    def close(self): self.db.close()

class _Cursor:
    def __init__(self, cursor): self.cursor = cursor
    def __enter__(self): return self
    def __exit__(self, *args): self.cursor.close()
    def close(self): self.cursor.close()
    def execute(self, sql, params=()):
        # This emulates insert-side NOT VALID FK enforcement only; it is NOT
        # evidence of native PostgreSQL DDL, locking or type compatibility.
        if sql.startswith("SELECT 1 FROM pg_constraint"):
            self.cursor.execute("SELECT 1 FROM sqlite_master WHERE name=?", (params[0],))
            return self
        fk = re.fullmatch(r"ALTER TABLE (\w+) ADD CONSTRAINT (\w+) FOREIGN KEY \((\w+)\) REFERENCES (\w+) \((\w+)\) NOT VALID", sql)
        if fk:
            table, name, column, parent, parent_column = fk.groups()
            self.cursor.execute(f"CREATE TRIGGER {name} BEFORE INSERT ON {table} WHEN NOT EXISTS (SELECT 1 FROM {parent} WHERE {parent_column}=NEW.{column}) BEGIN SELECT RAISE(ABORT,'missing ledger parent'); END")
            return self
        sql = sql.replace("%s", "?").replace("JSONB", "TEXT").replace("TIMESTAMPTZ", "TEXT").replace("BIGSERIAL", "INTEGER").replace(" FOR UPDATE", "")
        sql = re.sub(r"NOW\(\) - INTERVAL '([0-9]+) hours'", r"datetime('now','-\1 hours')", sql)
        sql = re.sub(r"NOW\(\) - INTERVAL '([0-9]+) days'", r"datetime('now','-\1 days')", sql)
        sql = sql.replace("NOW()", "CURRENT_TIMESTAMP")
        self.cursor.execute(sql, params); return self
    def fetchone(self): return self.cursor.fetchone()
    def fetchall(self): return self.cursor.fetchall()
    @property
    def rowcount(self): return self.cursor.rowcount

class PostgresBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = PostgresRepository("postgresql://fixture", connection=SQLiteDBAPIForPostgres(Path(self.tmp.name) / "fixture.db"))
        self.repo.initialize()
        self.t0 = "2026-01-01T00:00:00+00:00"
    def tearDown(self):
        self.repo._connection.db.close()
        self.tmp.cleanup()

    def test_sql_behavior_insert_read_duplicates_status_and_job(self):
        obs = ObservationRecord("o", "TEST", self.t0, "1", {"close": 100}, created_at=self.t0)
        dec = ShadowDecision("d", "o", "TEST", self.t0, "1", "BUY", {})
        outcome = replace(complete_label(dec, now="2026-01-02T00:00:00+00:00", entry_price=100, exit_price=101), outcome_id="x")
        ev = AdaptiveEvidence("e", "TEST", "1", "UNKNOWN", "production", 1, 1, 0, outcome.net_return, "OBSERVED", updated_at=outcome.matured_at)
        job = JobCheckpoint("j", "observation-generation", self.t0, checkpoint={"offset": 1}, last_updated=self.t0)
        self.repo.save_observation(obs); self.repo.save_observation(obs)
        self.repo.save_shadow_decision(dec); self.repo.save_shadow_decision(dec)
        self.repo.save_outcome(outcome); self.repo.save_outcome(outcome)
        self.assertEqual(self.repo.get_observation("o")["observation_id"], "o")
        self.assertEqual(self.repo.get_shadow_decision("d")["outcome_status"], "LABELLED")
        self.assertEqual(self.repo.get_outcome("x")["label"], "WIN")
        self.assertTrue(self.repo.contribute_adaptive_evidence(ev, "x"))
        self.assertFalse(self.repo.contribute_adaptive_evidence(ev, "x"))
        self.repo.save_job(job)
        self.assertEqual(self.repo.get_job("j")["checkpoint"]["offset"], 1)
        status = self.repo.learning_status()
        self.assertEqual(status["pending_outcomes"], 0)
        self.assertIn("latest_timestamps", status)

    def test_unavailable_outcome_and_retryable_job_are_persisted(self):
        obs = ObservationRecord("o", "TEST", self.t0, "1", {})
        dec = ShadowDecision("d", "o", "TEST", self.t0, "1", "BUY", {})
        self.repo.save_observation(obs); self.repo.save_shadow_decision(dec)
        outcome = replace(complete_label(dec, now="2026-01-02T00:00:00+00:00", entry_price=None, exit_price=None), outcome_id="u")
        job = JobCheckpoint("j2", "outcome-labelling", self.t0, "FAILED", "w", 2, {"cursor": 4}, True, "DATA_UNAVAILABLE", self.t0)
        self.repo.save_outcome(outcome); self.repo.save_job(job)
        self.assertEqual(self.repo.get_outcome("u")["data_quality"], "INCOMPLETE")
        self.assertTrue(self.repo.get_job("j2")["retryable"])

    def test_repository_reliability_round_trip(self):
        reliability = runtime_repository_reliability(self.repo)
        reliability.record_outcome(evidence_id="r", source_id="s", scope_key="global", horizon="5d", observed_at=self.t0, evaluated_at="2026-01-06T00:00:00+00:00", direction=1, forward_return=.1)
        reliability.record_outcome(evidence_id="r", source_id="s", scope_key="global", horizon="5d", observed_at=self.t0, evaluated_at="2026-01-06T00:00:00+00:00", direction=1, forward_return=.1)
        self.assertEqual(reliability.summarize("s").samples, 1)

if __name__ == "__main__": unittest.main()
