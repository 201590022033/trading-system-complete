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


def run(interval_seconds: float = 30.0, *, cycles=None, repository=None, handlers=None, schedulers=None) -> None:
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
        worker=ShadowWorker(repository,worker_id,selected)
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
    finally:
        if owned: repository.close()


if __name__ == "__main__":
    run()
