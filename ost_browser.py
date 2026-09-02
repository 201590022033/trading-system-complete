"""OST browser worker — runs as a separate process with its own HTTP API.

Why a process + HTTP (not stdio pipes): the dashboard runs under gevent's
monkey.patch_all(), which breaks subprocess stdin/stdout pipes on Windows
(OSError 22 in gevent's threadpool). A tiny HTTP server on 127.0.0.1:5051
sidesteps all of that.

Endpoints:
  POST /open            -> launch visible Chromium at the OST portal
  GET  /status          -> open/logged-in state
  POST /read            -> scrape cash + holdings from the logged-in portal
  POST /inspect         -> list amounts + nearby labels (calibration helper)
  POST /prepare-order   -> fill the order ticket (never submits)
  POST /close           -> shut down browser + this server

Start manually:  python ost_browser.py
The dashboard talks to it via ost_browser_client.py.

Pass 1/2 are read-only / form-fill-only: the worker never clicks the bank's
Confirm button and never sees credentials — the user logs in manually in the
visible window.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional

OST_HOME = "https://securities.standardbank.co.za/ost/"
LOGIN_MARKER = "VIEW_LOGIN_EVENT"
PROFILE_DIR = Path(__file__).parent / ".ost-browser-profile"
PORT = 5051

CASH_PATTERNS = [
    r"(?:available\s+(?:funds|cash)|cash\s+balance|available\s+to\s+invest|"
    r"trading\s+(?:account\s+)?(?:balance|funds)|jset\s+balance)"
    r"[^R0-9]{0,40}R?\s*([\d\s,]+\.\d{2})",
    r"R\s*([\d\s,]+\.\d{2})\s*(?:available|to invest)",
]


class Worker:
    def __init__(self):
        self.pw = None
        self.context = None

    # ---------- page helpers ----------

    def _pages(self):
        if self.context is None:
            return []
        try:
            return self.context.pages
        except Exception:
            return []

    def _active_page(self):
        """Pick the most portfolio-looking tab (OST opens the app in tab 2)."""
        pages = self._pages()
        if not pages:
            return None
        for p in pages:
            try:
                body = p.inner_text("body")[:6000].lower()
                if any(k in body for k in ("portfolio", "holdings", "available", "cash")):
                    return p
            except Exception:
                continue
        return pages[-1]

    def _detect_login(self) -> bool:
        page = self._active_page()
        if page is None:
            return False
        try:
            if LOGIN_MARKER.lower() in page.url.lower():
                return False
            if page.locator("input[type='password']").count() > 0:
                return False
            body = page.inner_text("body")[:8000].lower()
            return any(k in body for k in ("logout", "log out", "portfolio",
                                           "holdings", "account", "watchlist"))
        except Exception:
            return False

    # ---------- commands ----------

    def open(self) -> Dict:
        try:
            if self.pw is None:
                from playwright.sync_api import sync_playwright
                self.pw = sync_playwright().start()
            if self.context is None:
                PROFILE_DIR.mkdir(exist_ok=True)
                self.context = self.pw.chromium.launch_persistent_context(
                    str(PROFILE_DIR),
                    headless=False,
                    viewport={"width": 1280, "height": 900},
                )
            page = self._active_page()
            if page is None:
                page = self.context.new_page()
            page.goto(OST_HOME, timeout=30000, wait_until="domcontentloaded")
            page.bring_to_front()
            return {
                "ok": True, "open": True,
                "logged_in": self._detect_login(),
                "current_url": page.url,
                "message": "Browser open. Log in to OST in that window, then use Read Portfolio.",
            }
        except Exception as exc:
            return {"ok": False, "open": False, "message": f"Could not open browser: {exc}"}

    def status(self) -> Dict:
        if self.context is None:
            return {"ok": True, "open": False, "logged_in": False,
                    "message": "Browser not started."}
        if not self._pages():
            self._shutdown_browser()
            return {"ok": True, "open": False, "logged_in": False,
                    "message": "Browser window was closed."}
        page = self._active_page()
        logged_in = self._detect_login()
        return {
            "ok": True, "open": True, "logged_in": logged_in,
            "current_url": page.url if page else None,
            "message": "Logged in." if logged_in else "Open, waiting for OST login.",
        }

    def read(self) -> Dict:
        page = self._active_page()
        if page is None:
            return {"ok": False, "message": "Browser is not open."}
        try:
            if not self._detect_login():
                return {"ok": False, "logged_in": False,
                        "message": "Not logged in yet — complete the OST login in the browser window first."}

            navigated = self._try_navigate_to_portfolio(page)
            page = self._active_page()  # navigation may open a new tab
            body = page.inner_text("body")
            cash = self._extract_cash(body)
            holdings = self._extract_holdings(page)

            return {
                "ok": True, "logged_in": True, "url": page.url,
                "navigated_to_portfolio": navigated,
                "cash_available": cash,
                "holdings": holdings,
                "holdings_found": len(holdings),
                "message": ("Portfolio read." if (cash is not None or holdings)
                            else "Logged in, but no amounts matched. Click 'Inspect Labels' "
                                 "and paste the result back for calibration."),
            }
        except Exception as exc:
            return {"ok": False, "message": f"Read failed: {exc}"}

    @staticmethod
    def _safe_title(page) -> str:
        try:
            return page.title()
        except Exception:
            return ""

    def inspect(self) -> Dict:
        page = self._active_page()
        if page is None:
            return {"ok": False, "message": "Browser is not open."}
        try:
            body = page.inner_text("body")
        except Exception:
            # Tab may be mid-navigation — wait briefly and retry once
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                body = page.inner_text("body")
            except Exception as exc:
                return {"ok": False, "message": f"Page not readable yet (still loading?): {exc}"}
        try:
            lines = [ln.strip() for ln in body.splitlines() if ln.strip()]

            pairs = []
            for i, ln in enumerate(lines):
                if re.search(r"R\s*[\d\s,]+\.\d{2}", ln) or re.fullmatch(r"[\d\s,]+\.\d{2}", ln):
                    context = " | ".join(lines[max(0, i - 2):i + 1])
                    pairs.append(context[:220])

            tabs = []
            for p in self._pages():
                try:
                    tabs.append({"url": p.url, "title": self._safe_title(p)})
                except Exception:
                    pass

            return {
                "ok": True,
                "url": page.url,
                "title": self._safe_title(page),
                "tabs": tabs,
                "amount_contexts": pairs[:40],
                "message": f"{len(pairs)} amount contexts found across {len(tabs)} tab(s).",
            }
        except Exception as exc:
            return {"ok": False, "message": f"Inspect failed: {exc}"}

    def prepare_order(self, ticker: str, action: str, quantity: int) -> Dict:
        """Fill the OST order ticket. NEVER clicks submit/confirm."""
        page = self._active_page()
        if page is None:
            return {"ok": False, "message": "Browser is not open."}
        try:
            if not self._detect_login():
                return {"ok": False, "logged_in": False,
                        "message": "Not logged in — complete the OST login first."}

            ticker = ticker.upper().strip()
            action = action.lower().strip()
            if action not in ("buy", "sell"):
                return {"ok": False, "message": f"Invalid action: {action}"}

            steps: List[str] = []
            if not self._goto_order_ticket(page, ticker, steps):
                if self._search_and_open_stock(page, ticker, steps):
                    page = self._active_page()
                    self._goto_order_ticket(page, ticker, steps)
                else:
                    return {"ok": False, "calibration_needed": True, "steps": steps,
                            "current_url": page.url,
                            "message": "Could not find the order ticket. Open the Buy/Sell "
                                       "form manually in the browser, then retry."}

            page = self._active_page()
            fill = self._fill_order_form(page, ticker, action, quantity)
            steps.extend(fill["steps"])

            return {
                "ok": fill["filled"] >= 2,
                "calibration_needed": fill["filled"] < 2,
                "steps": steps,
                "current_url": page.url,
                "fields_filled": fill["filled"],
                "fields_missing": fill["missing"],
                "message": ("Form filled — REVIEW it and press the bank's own Confirm "
                            "button. Nothing was submitted by us."
                            if fill["filled"] >= 2 else
                            "Partial fill. Open the order form manually and retry, or "
                            "paste the Inspect Labels output so I can calibrate the fields."),
            }
        except Exception as exc:
            return {"ok": False, "message": f"Order prep failed: {exc}"}

    def close(self) -> Dict:
        self._shutdown_browser()
        return {"ok": True, "open": False, "logged_in": False, "message": "Browser closed."}

    def _shutdown_browser(self):
        try:
            if self.context is not None:
                self.context.close()
        except Exception:
            pass
        self.context = None
        try:
            if self.pw is not None:
                self.pw.stop()
        except Exception:
            pass
        self.pw = None

    # ---------- form helpers ----------

    @staticmethod
    def _try_navigate_to_portfolio(page) -> bool:
        for text in ("Portfolio", "Holdings", "My Portfolio", "Accounts"):
            try:
                link = page.get_by_text(text, exact=False).first
                if link.count() > 0:
                    link.click(timeout=4000)
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    def _extract_cash(body: str) -> Optional[float]:
        for pattern in CASH_PATTERNS:
            m = re.search(pattern, body, re.I)
            if m:
                raw = m.group(1).replace(" ", "").replace(",", "")
                try:
                    return float(raw)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _extract_holdings(page) -> List[Dict]:
        holdings: List[Dict] = []
        try:
            rows = page.locator("table tr")
            count = min(rows.count(), 60)
            for i in range(count):
                cells = rows.nth(i).locator("td")
                n = cells.count()
                if n < 3:
                    continue
                texts = [cells.nth(j).inner_text().strip() for j in range(n)]
                code = (texts[0] or "").upper().strip()
                if re.fullmatch(r"[A-Z0-9]{2,8}", code):
                    numbers = []
                    for t in texts[1:]:
                        cleaned = t.replace("R", "").replace(",", "").replace(" ", "").strip()
                        try:
                            numbers.append(float(cleaned))
                        except ValueError:
                            numbers.append(None)
                    holdings.append({"ticker": code, "raw": texts, "numbers": numbers})
        except Exception:
            pass
        return holdings

    def _goto_order_ticket(self, page, ticker: str, steps: List[str]) -> bool:
        for label in ("Buy", "Sell", "Trade", "Order", "Place Order", "New Order"):
            try:
                btn = page.get_by_role("button", name=re.compile(label, re.I)).first
                if btn.count() == 0:
                    btn = page.get_by_role("link", name=re.compile(label, re.I)).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=4000)
                    page.wait_for_load_state("domcontentloaded", timeout=8000)
                    steps.append(f"Clicked '{label}'")
                    return True
            except Exception:
                continue
        steps.append("No Buy/Sell/Trade control found on current page")
        return False

    def _search_and_open_stock(self, page, ticker: str, steps: List[str]) -> bool:
        try:
            search = None
            for ph in ("I'm looking for", "Search", "search"):
                loc = page.locator(f"input[placeholder*='{ph}' i]")
                if loc.count() > 0:
                    search = loc.first
                    break
            if search is None:
                steps.append("No search box found")
                return False
            search.fill(ticker)
            page.keyboard.press("Enter")
            page.wait_for_load_state("domcontentloaded", timeout=8000)
            steps.append(f"Searched for {ticker}")
            try:
                page.get_by_text(re.compile(ticker, re.I)).first.click(timeout=4000)
                page.wait_for_load_state("domcontentloaded", timeout=8000)
                steps.append(f"Opened {ticker} result")
            except Exception:
                steps.append("No clickable search result (may already be on the page)")
            return True
        except Exception as exc:
            steps.append(f"Search failed: {exc}")
            return False

    def _fill_order_form(self, page, ticker: str, action: str, quantity: int) -> Dict:
        filled = 0
        missing = []
        steps: List[str] = []

        # Action (buy/sell)
        try:
            action_loc = page.get_by_label(re.compile(action, re.I)).first
            if action_loc.count() > 0:
                if action_loc.get_attribute("type") == "radio":
                    action_loc.check(timeout=2000)
                else:
                    action_loc.click(timeout=2000)
                filled += 1
                steps.append(f"Set action: {action.upper()}")
            else:
                sel = page.locator("select").first
                if sel.count() > 0:
                    for o in sel.locator("option").all_inner_texts():
                        if action in o.lower():
                            sel.select_option(label=o)
                            filled += 1
                            steps.append(f"Set action via dropdown: {o}")
                            break
        except Exception:
            pass
        if filled == 0:
            missing.append("buy/sell selector")

        # Quantity
        qty_done = False
        for pattern in ("quant", "shares", "units", "volume", "amount"):
            try:
                loc = page.get_by_label(re.compile(pattern, re.I)).first
                if loc.count() > 0 and loc.is_visible():
                    loc.fill(str(quantity))
                    qty_done = True
                    filled += 1
                    steps.append(f"Set quantity: {quantity} (field '{pattern}')")
                    break
            except Exception:
                continue
        if not qty_done:
            try:
                nums = page.locator("input[type='number'], input[inputmode='numeric']")
                if nums.count() > 0:
                    nums.first.fill(str(quantity))
                    qty_done = True
                    filled += 1
                    steps.append(f"Set quantity: {quantity} (first numeric field)")
            except Exception:
                pass
        if not qty_done:
            missing.append("quantity field")

        # Instrument code
        try:
            inst = page.get_by_label(re.compile("instrument|security|share|code|stock", re.I)).first
            if inst.count() > 0 and inst.is_visible() and not inst.input_value():
                inst.fill(ticker)
                filled += 1
                steps.append(f"Set instrument: {ticker}")
        except Exception:
            pass

        return {"filled": filled, "missing": missing, "steps": steps}


# =========================
# HTTP wrapper
# =========================

worker = Worker()
shutdown_requested = False


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload: Dict, status: int = 200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> Dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode() or "{}")
        except json.JSONDecodeError:
            return {}

    def log_message(self, *args):  # silence request logging
        pass

    def do_GET(self):
        if self.path == "/status":
            self._send(worker.status())
        elif self.path == "/health":
            self._send({"ok": True})
        else:
            self._send({"ok": False, "message": "unknown endpoint"}, 404)

    def do_POST(self):
        global shutdown_requested
        try:
            data = self._body()

            if self.path == "/open":
                self._send(worker.open())
            elif self.path == "/read":
                self._send(worker.read())
            elif self.path == "/inspect":
                self._send(worker.inspect())
            elif self.path == "/prepare-order":
                self._send(worker.prepare_order(
                    ticker=data.get("ticker", ""),
                    action=data.get("action", ""),
                    quantity=int(data.get("quantity", 0) or 0),
                ))
            elif self.path == "/close":
                self._send(worker.close())
                shutdown_requested = True
            else:
                self._send({"ok": False, "message": "unknown endpoint"}, 404)
        except Exception as exc:
            # Never let the worker die without answering — the dashboard needs
            # a response even when the page is in a weird state.
            try:
                self._send({"ok": False, "message": f"Worker error: {exc}"})
            except Exception:
                pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"ost_browser worker listening on 127.0.0.1:{PORT}", flush=True)
    while not shutdown_requested:
        server.handle_request()
    worker._shutdown_browser()


if __name__ == "__main__":
    main()
