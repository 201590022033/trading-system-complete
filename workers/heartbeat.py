"""Infrastructure-only worker heartbeat; no market, source, or broker work."""

from datetime import datetime, timezone
import json
import os
import time
import uuid


def heartbeat(worker_id: str | None = None) -> dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    return {"worker_id": worker_id or os.environ.get("WORKER_ID", uuid.uuid4().hex),
            "started_at": now, "last_heartbeat_at": now, "status": "RUNNING",
            "mode": os.environ.get("APP_MODE", "DEVELOPMENT").upper(), "version": os.environ.get("COMMIT_SHA", "unknown")}


def run(interval_seconds: float = 30.0, *, cycles=None, repository=None, handlers=None) -> None:
    from workers.shadow_learning import ShadowWorker, configured_repository
    from workers.runtime import runtime_handlers
    owned=repository is None
    repository=repository or configured_repository()
    worker_id = os.environ.get("WORKER_ID", uuid.uuid4().hex)
    worker=ShadowWorker(repository,worker_id,handlers if handlers is not None else runtime_handlers(repository))
    count=0
    try:
        while cycles is None or count<cycles:
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
