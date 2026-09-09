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


def run(interval_seconds: float = 30.0) -> None:
    worker_id = os.environ.get("WORKER_ID", uuid.uuid4().hex)
    while True:
        print(json.dumps(heartbeat(worker_id), sort_keys=True), flush=True)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run()
