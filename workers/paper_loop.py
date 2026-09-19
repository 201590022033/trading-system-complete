"""Bounded durable scheduling. The injected processor can only use frozen input."""
from datetime import datetime, timezone
from shadow_learning import JobCheckpoint, stable_id, timestamp


class PaperScheduler:
    def __init__(self, repository, account_id, *, interval_seconds=300):
        if not account_id or not isinstance(interval_seconds, int) or interval_seconds < 60:
            raise ValueError("bounded interval and paper account required")
        self.repository, self.account_id, self.interval = repository, account_id, interval_seconds

    def enqueue(self, now):
        at = timestamp(now)
        bucket = int(at.timestamp()) // self.interval * self.interval
        target = datetime.fromtimestamp(bucket, timezone.utc).isoformat()
        job = JobCheckpoint(stable_id("paper-cycle", self.account_id, target),
                            "paper-cycle", target, checkpoint={"account_id": self.account_id})
        self.repository.ensure_job(job)
        return job


class FrozenPaperHandler:
    def __init__(self, repository, account_id, loader, processor, clock):
        self.repository, self.account_id = repository, account_id
        self.loader, self.processor, self.clock = loader, processor, clock

    def __call__(self, job):
        if job.checkpoint.get("account_id") != self.account_id:
            raise ValueError("paper account job mismatch")
        rid = stable_id("paper-input", job.job_key)
        frozen = self.repository.paper_record(rid)
        if frozen is None:
            supplied = self.loader()
            now = timestamp(self.clock()).isoformat()
            # Lock serializes competing attempts; the first frozen input wins.
            with self.repository.paper_account_transaction(self.account_id):
                frozen = self.repository.paper_record(rid)
                if frozen is None:
                    frozen = {"evaluated_at": now, "input": supplied, "job_key": job.job_key}
                    self.repository.save_paper_record(rid, self.account_id, "input", now, frozen)
        return self.processor(job.job_key, frozen)
