"""Client for the OST browser worker's HTTP API (127.0.0.1:5051).

The worker process (ost_browser.py) can be started manually, or this client
will spawn it on first use. Plain HTTP calls — no pipes — so it's safe under
the dashboard's gevent monkey-patching.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

WORKER = Path(__file__).parent / "ost_browser.py"
BASE = "http://127.0.0.1:5051"


class OSTBrowserClient:
    def __init__(self, python_exe: Optional[str] = None):
        self.python_exe = python_exe or sys.executable

    # ---------- transport ----------

    def _call(self, method: str, path: str, payload: Optional[Dict] = None,
              timeout: float = 60.0) -> Dict:
        self._ensure_worker()
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            BASE + path, data=body, method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            return {"ok": False, "message": f"Browser worker unreachable: {exc}"}
        except Exception as exc:
            return {"ok": False, "message": f"Browser call failed: {exc}"}

    def _worker_alive(self) -> bool:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _ensure_worker(self):
        if self._worker_alive():
            return
        # Spawn detached so it survives independently of the Flask process
        subprocess.Popen(
            [self.python_exe, str(WORKER)],
            cwd=str(WORKER.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        # Wait for the health endpoint
        import time
        for _ in range(50):
            if self._worker_alive():
                return
            time.sleep(0.2)

    # ---------- commands ----------

    def open(self) -> Dict:
        return self._call("POST", "/open", {}, timeout=60)

    def status(self) -> Dict:
        return self._call("GET", "/status", timeout=15)

    def read_portfolio(self) -> Dict:
        return self._call("POST", "/read", {}, timeout=45)

    def inspect(self) -> Dict:
        return self._call("POST", "/inspect", {}, timeout=30)

    def prepare_order(self, ticker: str, action: str, quantity: int) -> Dict:
        return self._call("POST", "/prepare-order",
                          {"ticker": ticker, "action": action, "quantity": quantity},
                          timeout=90)

    def close(self) -> Dict:
        if not self._worker_alive():
            return {"ok": True, "open": False, "logged_in": False,
                    "message": "Browser not running."}
        return self._call("POST", "/close", {}, timeout=30)


# Singleton for the Flask app
ost_browser_client = OSTBrowserClient()
