"""Parent-side manager for the OST browser worker process.

Spawns ost_browser.py as a subprocess and speaks JSON-lines over its
stdin/stdout. Safe to call from the gevent-based dashboard app because all
the Playwright work happens in the child process.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, Optional

WORKER = Path(__file__).parent / "ost_browser.py"


class OSTBrowserClient:
    """Controls the browser worker subprocess from the dashboard app."""

    def __init__(self, python_exe: Optional[str] = None):
        self.python_exe = python_exe or sys.executable
        self._proc: Optional[subprocess.Popen] = None
        self._write_lock = threading.Lock()

    def _ensure_proc(self):
        if self._proc is not None and self._proc.poll() is None:
            return
        self._proc = subprocess.Popen(
            [self.python_exe, str(WORKER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(WORKER.parent),
        )

    def _command(self, cmd: str, timeout_lines: int = 200, **params) -> Dict:
        try:
            self._ensure_proc()
            with self._write_lock:
                self._proc.stdin.write(json.dumps({"cmd": cmd, **params}) + "\n")
                self._proc.stdin.flush()
                # Read lines until we get a JSON response (skip LOG: lines)
                for _ in range(timeout_lines):
                    line = self._proc.stdout.readline()
                    if not line:
                        return {"ok": False, "message": "Browser worker stopped responding."}
                    line = line.strip()
                    if line.startswith("LOG:"):
                        continue
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {"ok": False, "message": "Browser worker response timeout."}
        except Exception as exc:
            return {"ok": False, "message": f"Browser control failed: {exc}"}

    def open(self) -> Dict:
        return self._command("open")

    def status(self) -> Dict:
        return self._command("status")

    def read_portfolio(self) -> Dict:
        return self._command("read")

    def prepare_order(self, ticker: str, action: str, quantity: int) -> Dict:
        return self._command("prepare_order", ticker=ticker, action=action,
                             quantity=quantity)

    def close(self) -> Dict:
        resp = self._command("close")
        if self._proc is not None:
            try:
                self._proc.wait(timeout=10)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
        return resp


# Singleton for the Flask app
ost_browser_client = OSTBrowserClient()
