"""Bounded, restart-safe orchestration primitives for shadow learning.

Handlers are injected by the host; no broker or network work is performed here.
"""
from datetime import datetime, timezone
from shadow_learning import JobCheckpoint
from runtime_persistence import runtime_repository

JOB_TYPES = ("market-data-update", "market-intelligence-refresh", "observation-generation",
             "shadow-decision-generation", "outcome-labelling", "adaptive-evidence-update")

def configured_repository(*, database_url=None, sqlite_path="market_intelligence.db"):
    return runtime_repository(database_url=database_url, sqlite_path=sqlite_path)

class ShadowWorker:
    def __init__(self, repository, worker_id: str, handlers: dict | None = None):
        self.repository, self.worker_id, self.handlers = repository, worker_id, handlers or {}

    def run_once(self, jobs: list[JobCheckpoint]) -> int:
        processed = 0
        for job in jobs:
            if job.job_type not in JOB_TYPES or job.status == "COMPLETED":
                continue
            now = datetime.now(timezone.utc).isoformat()
            running = JobCheckpoint(job.job_key, job.job_type, job.target_time, "RUNNING",
                                    self.worker_id, job.attempt_count + 1, job.checkpoint,
                                    job.retryable, job.error_category, now)
            self.repository.save_job(running)
            try:
                handler = self.handlers.get(job.job_type)
                checkpoint = handler(job) if handler else job.checkpoint
                done = JobCheckpoint(job.job_key, job.job_type, job.target_time, "COMPLETED",
                                     self.worker_id, running.attempt_count, checkpoint, job.retryable, None,
                                     datetime.now(timezone.utc).isoformat())
            except Exception as exc:
                done = JobCheckpoint(job.job_key, job.job_type, job.target_time, "FAILED",
                                     self.worker_id, running.attempt_count, job.checkpoint, job.retryable,
                                     type(exc).__name__, datetime.now(timezone.utc).isoformat())
            self.repository.save_job(done)
            processed += 1
        return processed

    def recover_running(self, jobs: list[JobCheckpoint]) -> list[JobCheckpoint]:
        """Make abandoned retryable work visible after a worker restart."""
        recovered = []
        for job in jobs:
            if job.status == "RUNNING" and job.retryable:
                item = JobCheckpoint(job.job_key, job.job_type, job.target_time, "PENDING",
                                     None, job.attempt_count, job.checkpoint, True,
                                     "WORKER_RESTART", datetime.now(timezone.utc).isoformat())
                self.repository.save_job(item); recovered.append(item)
        return recovered
