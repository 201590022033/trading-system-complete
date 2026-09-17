"""Bounded, restart-safe orchestration primitives for shadow learning.

Handlers are injected by the host; no broker or network work is performed here.
"""
from datetime import datetime, timezone
from dataclasses import replace
from itertools import islice
from shadow_learning import JobCheckpoint
from runtime_persistence import runtime_repository

JOB_TYPES = ("market-data-update", "market-intelligence-refresh", "observation-generation",
             "shadow-decision-generation", "outcome-labelling", "adaptive-evidence-update")

def configured_repository(*, database_url=None, sqlite_path="market_intelligence.db"):
    return runtime_repository(database_url=database_url, sqlite_path=sqlite_path)

class ShadowWorker:
    def __init__(self, repository, worker_id: str, handlers: dict | None = None, *, max_jobs=1, clock=None, lease_seconds=300):
        if not 1<=max_jobs<=100: raise ValueError('bounded job limit required')
        self.repository, self.worker_id, self.handlers = repository, worker_id, handlers or {}
        from reliability_store import runtime_repository_reliability
        self.reliability=runtime_repository_reliability(repository)
        self.max_jobs,self.lease_seconds=max_jobs,lease_seconds
        self.clock=clock or (lambda:datetime.now(timezone.utc).isoformat())

    def run_once(self, jobs=None) -> int:
        now=self.clock()
        if jobs is not None:
            for job in islice(jobs,self.max_jobs): self.repository.ensure_job(job)
        self.repository.recover_jobs(now,limit=self.max_jobs,lease_seconds=self.lease_seconds)
        processed = 0
        for candidate in self.repository.due_jobs(now,self.max_jobs):
            running=self.repository.claim_job(candidate.job_key,self.worker_id,now)
            if running is None: continue
            handler=self.handlers.get(running.job_type)
            if handler is None or running.job_type not in JOB_TYPES:
                done=replace(running,status='FAILED',retryable=False,error_category='MISSING_HANDLER',last_updated=self.clock())
            else:
                try:
                    checkpoint=handler(running)
                    if not isinstance(checkpoint,dict): raise ValueError('checkpoint must be a mapping')
                    done=replace(running,status='COMPLETED',checkpoint=checkpoint,error_category=None,last_updated=self.clock())
                except Exception:
                    done=replace(running,status='FAILED',error_category='HANDLER_FAILED',last_updated=self.clock())
            self.repository.finish_job(running,done)
            processed += 1
        return processed

    def recover_running(self, jobs: list[JobCheckpoint]) -> list[JobCheckpoint]:
        """Make abandoned retryable work visible after a worker restart."""
        keys={job.job_key for job in islice(jobs,self.max_jobs)}
        return self.repository.recover_jobs(self.clock(),limit=self.max_jobs,
            lease_seconds=self.lease_seconds,keys=keys)
