"""Shared durable PAPER ledger; no backend fallback and no external broker."""
import json
from contextlib import contextmanager
from shadow_learning import timestamp


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class PaperLedger:
    def create_paper_account(self, account_id, initial):
        if not account_id or initial.get("mode") != "PAPER":
            raise ValueError("explicit PAPER account required")
        with self.transaction():
            self._job_sql("INSERT INTO paper_accounts VALUES (?,?,?) ON CONFLICT(account_id) DO NOTHING",
                          (account_id, 0, encode(initial)))

    @contextmanager
    def paper_account_transaction(self, account_id):
        with self.transaction():
            suffix = " FOR UPDATE" if self.backend == "postgresql" else ""
            rows = self._job_sql("SELECT revision,payload FROM paper_accounts WHERE account_id=?" + suffix,
                                 (account_id,), rows=True)
            if not rows:
                raise ValueError("paper account not configured")
            revision, raw = rows[0]
            state = json.loads(raw)
            yield state
            changed = self._job_sql(
                "UPDATE paper_accounts SET revision=?,payload=? WHERE account_id=? AND revision=?",
                (revision + 1, encode(state), account_id, revision))
            if changed != 1:
                raise RuntimeError("paper account concurrent update")

    def paper_account(self, account_id):
        rows = self._job_sql("SELECT payload FROM paper_accounts WHERE account_id=?",
                             (account_id,), rows=True)
        return json.loads(rows[0][0]) if rows else None

    def save_paper_record(self, record_id, account_id, kind, available_at, payload):
        at = timestamp(available_at).isoformat()
        serialized = encode(payload)
        with self.transaction():
            self._job_sql("INSERT INTO paper_records VALUES (?,?,?,?,?) ON CONFLICT(record_id) DO NOTHING",
                         (record_id, account_id, kind, at, serialized))
            rows = self._job_sql("SELECT account_id,kind,available_at,payload FROM paper_records WHERE record_id=?",
                                 (record_id,), rows=True)
            if tuple(rows[0]) != (account_id, kind, at, serialized):
                raise ValueError("conflicting immutable paper record")

    def paper_record(self, record_id):
        rows = self._job_sql("SELECT payload FROM paper_records WHERE record_id=?", (record_id,), rows=True)
        return json.loads(rows[0][0]) if rows else None

    def paper_records(self, account_id, kind, *, as_of, limit=400):
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("bounded paper query required")
        rows = self._job_sql(
            "SELECT payload FROM paper_records WHERE account_id=? AND kind=? AND available_at<=? "
            "ORDER BY available_at DESC,record_id DESC LIMIT ?",
            (account_id, kind, timestamp(as_of).isoformat(), limit), rows=True)
        return [json.loads(row[0]) for row in rows]
