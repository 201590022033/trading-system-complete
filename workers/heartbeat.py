"""Bounded durable worker heartbeat; configured paper work never calls live brokers."""

from datetime import datetime, timezone
import json
import os
import time
import uuid


def heartbeat(worker_id: str | None = None) -> dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    return {"worker_id": worker_id or os.environ.get("WORKER_ID", uuid.uuid4().hex),
            "started_at": now, "last_heartbeat_at": now, "status": "RUNNING",
            "mode": os.environ.get("APP_MODE", "DEVELOPMENT").upper(), "version": os.environ.get("RAILWAY_GIT_COMMIT_SHA") or os.environ.get("COMMIT_SHA", "unknown")}


def run(interval_seconds: float = 30.0, *, cycles=None, repository=None, handlers=None, schedulers=None, scheduled=False) -> None:
    from workers.shadow_learning import ShadowWorker, configured_repository
    from workers.runtime import runtime_handlers
    owned=repository is None
    repository=repository or configured_repository()
    worker_id = os.environ.get("WORKER_ID", uuid.uuid4().hex)
    try:
        selected = handlers if handlers is not None else runtime_handlers(repository)
        scheduler_list = list(schedulers) if schedulers is not None else []
        if handlers is None:
            from application.opportunities.paper_host import configured_paper, compose_paper_worker
            config = configured_paper()
            if config:
                scheduler, handler = compose_paper_worker(repository, config)
                selected["paper-cycle"] = handler
                scheduler_list.append(scheduler)
            from workers.ig_streaming import compose_ig_stream_worker
            scheduler, handler = compose_ig_stream_worker(repository)
            if scheduler is not None:
                selected["ig-stream-ingestion"] = handler
                scheduler_list.append(scheduler)
        worker=ShadowWorker(repository,worker_id,selected, max_jobs=10 if scheduled else 1)
        run_started_at = datetime.now(timezone.utc).isoformat()
        if scheduled:
            cycles = 1
        count=0
        while cycles is None or count<cycles:
            now = datetime.now(timezone.utc).isoformat()
            for scheduler in scheduler_list:
                scheduler.enqueue(now)
            processed=worker.run_once()
            status={**heartbeat(worker_id),'processed':processed}
            repository.save_worker_status(status)
            print(json.dumps(status,sort_keys=True),flush=True)
            count+=1
            if cycles is None or count<cycles: time.sleep(max(1,interval_seconds))
        if scheduled:
            if os.environ.get("SWING_RESEARCH_ENABLED") == "1":
                from application.opportunities.swing_research import run_research
                research = run_research(repository, datetime.now(timezone.utc))
                print(json.dumps({"swing_research_state": research["state"], "live_execution": False}), flush=True)
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            failures = repository._job_sql("SELECT COUNT(*) FROM worker_jobs WHERE status='FAILED' AND last_updated>=?",
                                           (run_started_at,), rows=True)[0][0]
            if failures:
                repository.save_worker_status({**heartbeat(worker_id), "status": "FAILED",
                                              "processed": processed})
                raise RuntimeError("scheduled worker job failed; inspect sanitized job state")
            from application.opportunities.paper_host import configured_paper
            config = configured_paper()
            if config:
                repository.archive_paper_inputs(config.account_id, before=(now-timedelta(days=90)).isoformat())
            cron_hour = int(os.environ.get("SWING_WORKER_CRON_HOUR", "0"))
            if not 0 <= cron_hour <= 23:
                raise ValueError("valid UTC cron hour required")
            next_run = now.replace(hour=cron_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            repository.save_worker_status({**heartbeat(worker_id), "status": "SCHEDULED_IDLE",
                "schedule": f"0 {cron_hour} * * *", "next_scheduled_at": next_run.isoformat(),
                "processed": processed})
    finally:
        if owned: repository.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scheduled", action="store_true", help="process bounded due jobs, then exit")
    run(scheduled=parser.parse_args().scheduled)
