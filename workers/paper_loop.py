"""Bounded durable scheduling. The injected processor can only use frozen input."""
from datetime import datetime, timezone
from shadow_learning import JobCheckpoint, stable_id, timestamp
from domain.strategy.attribution import freeze_profile, validate_frozen_profile, fields


class PaperScheduler:
    def __init__(self, repository, account_id, *, interval_seconds=300, strategy_profile=None):
        if not account_id or not isinstance(interval_seconds, int) or interval_seconds < 60:
            raise ValueError("bounded interval and paper account required")
        self.repository, self.account_id, self.interval = repository, account_id, interval_seconds
        self.strategy = freeze_profile(strategy_profile) if strategy_profile is not None else {}

    def enqueue(self, now):
        at = timestamp(now)
        bucket = int(at.timestamp()) // self.interval * self.interval
        target = datetime.fromtimestamp(bucket, timezone.utc).isoformat()
        if self.strategy:
            self.repository.save_strategy_definition(self.strategy)
        job = JobCheckpoint(stable_id("paper-cycle", self.account_id, target),
                            "paper-cycle", target, checkpoint={"account_id": self.account_id,
                                **{k: v for k, v in self.strategy.items() if k != "strategy_profile_snapshot"}})
        self.repository.ensure_job(job)
        # A pre-upgrade job in this bucket keeps its original legacy checkpoint.
        return JobCheckpoint(**self.repository.get_job(job.job_key))


class FrozenPaperHandler:
    def __init__(self, repository, account_id, loader, processor, clock):
        self.repository, self.account_id = repository, account_id
        self.loader, self.processor, self.clock = loader, processor, clock

    def __call__(self, job):
        from domain.strategy.attribution import reference
        strategy = reference(job.checkpoint)
        definition = self.repository.strategy_definition(**strategy.to_dict()) if strategy else None
        validate_frozen_profile(job.checkpoint, definition=definition)
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
                    frozen = {"evaluated_at": now, "input": supplied, "job_key": job.job_key,
                              **({key: job.checkpoint[key] for key in (
                                  "strategy_profile_id", "strategy_profile_version",
                                  "strategy_profile_sha256", "strategy_attribution_schema")} if strategy else {})}
                    self.repository.save_paper_record(rid, self.account_id, "input", now, frozen)
        from domain.strategy.attribution import same_strategy
        same_strategy(job.checkpoint, frozen)
        validate_frozen_profile(frozen, definition=definition)
        return self.processor(job.job_key, frozen)
