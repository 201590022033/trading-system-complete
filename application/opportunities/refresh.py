"""Single bounded, on-demand public research refresh for the dashboard."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Lock

from .public_research import refresh_public_research


class OpportunityRefresh:
    def __init__(self, service, runner=refresh_public_research):
        self.service = service
        self.runner = runner
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="canonical-research")
        self._lock = Lock()
        self._running = False
        self._last_started = None
        self._last_completed = None
        self._scanned = 0
        self._unranked = 0
        self._unavailable = ()
        self._state = "NOT_RUN"

    def status(self):
        with self._lock:
            return {"state": self._state, "running": self._running,
                    "last_completed": self._last_completed.isoformat() if self._last_completed else None,
                    "scanned": self._scanned, "unranked": self._unranked,
                    "unavailable": list(self._unavailable)}

    def trigger(self):
        now = datetime.now(timezone.utc)
        with self._lock:
            if self._running or (self._last_started and now - self._last_started < timedelta(minutes=5)):
                return self.status_unlocked()
            self._running = True
            self._state = "LOADING"
            self._last_started = now
            self._pool.submit(self._run)
            return self.status_unlocked()

    def status_unlocked(self):
        return {"state": self._state, "running": self._running,
                "last_completed": self._last_completed.isoformat() if self._last_completed else None,
                "scanned": self._scanned, "unranked": self._unranked,
                "unavailable": list(self._unavailable)}

    def _run(self):
        try:
            result = self.runner()
            ranked = tuple(item for item in result.opportunities if item.rank is not None)
            with self._lock:
                self.service.replace_records(ranked)
                self._scanned = result.scanned
                self._unranked = len(result.opportunities) - len(ranked)
                self._unavailable = result.unavailable
                self._last_completed = datetime.now(timezone.utc)
                self._state = "AVAILABLE" if ranked else "INSUFFICIENT_EVIDENCE"
        except Exception:
            with self._lock:
                self.service.replace_records()
                self._state = "UNAVAILABLE"
        finally:
            with self._lock:
                self._running = False
