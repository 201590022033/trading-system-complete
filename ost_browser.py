"""OST browser worker process.

Runs as a SEPARATE PROCESS (not a thread) because Playwright's sync API
conflicts with gevent's monkey-patching in the dashboard app.

Communication: a tiny JSON-lines control channel over stdin/stdout.
The dashboard app spawns this process and sends one command per line:

  {"cmd": "open"}     -> launch visible Chromium at the OST portal
  {"cmd": "status"}   -> report open/logged-in state
  {"cmd": "read"}     -> scrape cash + holdings from the logged-in portal
  {"cmd": "close"}    -> shut down

Each command gets exactly one JSON response line on stdout.
Log/diagnostic lines are prefixed with "LOG:" so the parent can ignore them.

Pass 1 is read-only: it never clicks order buttons and never sees your
credentials — you type them into the visible browser window yourself.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

OST_HOME = "https://securities.standardbank.co.za/ost/"
LOGIN_MARKER = "VIEW_LOGIN_EVENT"
PROFILE_DIR = Path(__file__).parent / ".ost-browser-profile"

CASH_PATTERNS = [
    r"(?:available\s+(?:funds|cash)|cash\s+balance|available\s+to\s+invest)"
    r"[^R0-9]{0,40}R?\s*([\d\s,]+\.\d{2})",
    r"R\s*([\d\s,]+\.\d{2})\s*(?:available)",
]


def log(msg: str):
    print(f"LOG:{msg}", flush=True)


class Worker:
    def __init__(self):
        self.pw = None
        self.context = None
        self.page = None

    # ---------- lifecycle ----------

    def open(self) -> Dict:
        try:
            if self.pw is None:
                from playwright.sync_api import sync_playwright
                self.pw = sync_playwright().start()
            if self.context is None:
                PROFILE_DIR.mkdir(exist_ok=True)
                self.context = self.pw.chromium.launch_persistent_context(
                    str(PROFILE_DIR),
                    headless=False,  # visible: the user logs in themselves
                    viewport={"width": 1280, "height": 900},
                )
                self.page = (
                    self.context.pages[0] if self.context.pages else self.context.new_page()
                )
            if self.page is None:
                self.page = self.context.new_page()
            self.page.goto(OST_HOME, timeout=30000, wait_until="domcontentloaded")
            logged_in = self._detect_login()
            return {
                "ok": True,
                "open": True,
                "logged_in": logged_in,
                "current_url": self.page.url,
                "message": "Browser open. Log in to OST in the window, then read the portfolio.",
            }
        except Exception as exc:
            return {"ok": False, "open": False, "message": f"Could not open browser: {exc}"}

    def status(self) -> Dict:
        if self.context is None:
            return {"ok": True, "open": False, "logged_in": False,
                    "message": "Browser not started."}
        try:
            if not self.context.pages:
                self.context = None
                self.page = None
                return {"ok": True, "open": False, "logged_in": False,
                        "message": "Browser window was closed."}
            logged_in = self._detect_login()
            return {
                "ok": True,
                "open": True,
                "logged_in": logged_in,
                "current_url": self.page.url,
                "message": "Logged in." if logged_in else "Open, waiting for OST login.",
            }
        except Exception as exc:
            return {"ok": False, "open": False, "message": f"Status check failed: {exc}"}

    def close(self) -> Dict:
        try:
            if self.context is not None:
                self.context.close()
        except Exception:
            pass
        self.context = None
        self.page = None
        if self.pw is not None:
            try:
                self.pw.stop()
            except Exception:
                pass
            self.pw = None
        return {"ok": True, "open": False, "logged_in": False, "message": "Browser closed."}

    # ---------- order ticket (Pass 2: auto-fill, human confirms) ----------

    def prepare_order(self, ticker: str, action: str, quantity: int) -> Dict:
        """Navigate to the OST order ticket and pre-fill it.

        SAFETY: this NEVER clicks the final submit/confirm button. It fills
        the form and leaves the cursor on the bank's own confirm control for
        the human to press.
        """
        if self.page is None:
            return {"ok": False, "message": "Browser is not open."}
        try:
            if not self._detect_login():
                return {"ok": False, "logged_in": False,
                        "message": "Not logged in — complete the OST login first."}

            ticker = ticker.upper().strip()
            action = action.lower().strip()
            if action not in ("buy", "sell"):
                return {"ok": False, "message": f"Invalid action: {action}"}

            steps = []

            # 1) Navigate to the order/trade page
            if self._goto_order_ticket(ticker, steps):
                steps.append(f"On order page: {self.page.url}")
            else:
                # Fall back to the stock-search route
                if self._search_and_open_stock(ticker, steps):
                    steps.append(f"Opened {ticker} page: {self.page.url}")
                    self._goto_order_ticket(ticker, steps)
                else:
                    return {
                        "ok": False,
                        "calibration_needed": True,
                        "steps": steps,
                        "current_url": self.page.url,
                        "message": "Could not find the order ticket. Open the "
                                   "Buy/Sell form for this share manually in the "
                                   "browser, then click 'Fill Form' again.",
                    }

            # 2) Fill the form
            fill = self._fill_order_form(ticker, action, quantity)
            steps.extend(fill["steps"])

            return {
                "ok": fill["filled"] >= 2,
                "calibration_needed": fill["filled"] < 2,
                "steps": steps,
                "current_url": self.page.url,
                "fields_filled": fill["filled"],
                "fields_missing": fill["missing"],
                "message": (
                    "Form filled — REVIEW it and press the bank's own "
                    "Confirm/Submit button. Nothing was submitted by us."
                    if fill["filled"] >= 2
                    else "Partial fill. Open the order form manually, then try "
                         "'Fill Form' again — or tell me the exact field labels "
                         "you see and I'll calibrate."
                ),
            }
        except Exception as exc:
            return {"ok": False, "message": f"Order prep failed: {exc}"}

    def _goto_order_ticket(self, ticker: str, steps: List[str]) -> bool:
        """Find and click a Buy/Sell/Trade control."""
        for label in ("Buy", "Sell", "Trade", "Order", "Place Order", "New Order"):
            try:
                btn = self.page.get_by_role("button", name=re.compile(label, re.I)).first
                if btn.count() == 0:
                    btn = self.page.get_by_role("link", name=re.compile(label, re.I)).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=4000)
                    self.page.wait_for_load_state("domcontentloaded", timeout=8000)
                    steps.append(f"Clicked '{label}'")
                    return True
            except Exception:
                continue
        steps.append("No Buy/Sell/Trade control found on current page")
        return False

    def _search_and_open_stock(self, ticker: str, steps: List[str]) -> bool:
        """Use the OST stock search to open the instrument page."""
        try:
            search = None
            for ph in ("I'm looking for", "Search", "search"):
                loc = self.page.locator(f"input[placeholder*='{ph}' i]")
                if loc.count() > 0:
                    search = loc.first
                    break
            if search is None:
                steps.append("No search box found")
                return False
            search.fill(ticker)
            self.page.keyboard.press("Enter")
            self.page.wait_for_load_state("domcontentloaded", timeout=8000)
            steps.append(f"Searched for {ticker}")
            # Try to click the first result containing the ticker
            try:
                self.page.get_by_text(re.compile(ticker, re.I)).first.click(timeout=4000)
                self.page.wait_for_load_state("domcontentloaded", timeout=8000)
                steps.append(f"Opened {ticker} result")
            except Exception:
                steps.append("No clickable search result (may already be on the page)")
            return True
        except Exception as exc:
            steps.append(f"Search failed: {exc}")
            return False

    def _fill_order_form(self, ticker: str, action: str, quantity: int) -> Dict:
        """Fill whatever order form is currently visible. Never submits."""
        filled = 0
        missing = []
        steps: List[str] = []

        # Action (buy/sell): radio, select, or button toggle
        try:
            action_loc = self.page.get_by_label(re.compile(action, re.I)).first
            if action_loc.count() > 0:
                action_loc.check(timeout=2000) if action_loc.get_attribute("type") == "radio" else action_loc.click(timeout=2000)
                filled += 1
                steps.append(f"Set action: {action.upper()}")
            else:
                sel = self.page.locator("select").first
                if sel.count() > 0:
                    opts = sel.locator("option").all_inner_texts()
                    for o in opts:
                        if action in o.lower():
                            sel.select_option(label=o)
                            filled += 1
                            steps.append(f"Set action via dropdown: {o}")
                            break
        except Exception:
            pass
        if filled == 0:
            missing.append("buy/sell selector")

        # Quantity: any visible number input labelled quantity/shares/units/volume
        qty_done = False
        for pattern in ("quant", "shares", "units", "volume", "amount"):
            try:
                loc = self.page.get_by_label(re.compile(pattern, re.I)).first
                if loc.count() > 0 and loc.is_visible():
                    loc.fill(str(quantity))
                    qty_done = True
                    filled += 1
                    steps.append(f"Set quantity: {quantity} (field matched '{pattern}')")
                    break
            except Exception:
                continue
        if not qty_done:
            # Last resort: the only visible numeric text input on the form
            try:
                nums = self.page.locator("input[type='number'], input[inputmode='numeric']")
                if nums.count() > 0:
                    nums.first.fill(str(quantity))
                    qty_done = True
                    filled += 1
                    steps.append(f"Set quantity: {quantity} (first numeric field)")
            except Exception:
                pass
        if not qty_done:
            missing.append("quantity field")

        # Ticker/instrument field (some forms have one even after navigation)
        try:
            inst = self.page.get_by_label(re.compile("instrument|security|share|code|stock", re.I)).first
            if inst.count() > 0 and inst.is_visible() and not inst.input_value():
                inst.fill(ticker)
                filled += 1
                steps.append(f"Set instrument: {ticker}")
        except Exception:
            pass

        return {"filled": filled, "missing": missing, "steps": steps}

    # ---------- read ----------

    def read(self) -> Dict:
        if self.page is None:
            return {"ok": False, "message": "Browser is not open."}
        try:
            if not self._detect_login():
                return {
                    "ok": False,
                    "logged_in": False,
                    "message": "Not logged in yet — complete the OST login in the "
                               "browser window first.",
                }

            navigated = self._try_navigate_to_portfolio()
            body = self.page.inner_text("body")
            cash = self._extract_cash(body)
            holdings = self._extract_holdings()

            return {
                "ok": True,
                "logged_in": True,
                "url": self.page.url,
                "navigated_to_portfolio": navigated,
                "cash_available": cash,
                "holdings": holdings,
                "holdings_found": len(holdings),
                "message": (
                    "Portfolio read."
                    if (cash is not None or holdings)
                    else "Logged in, but no portfolio table found on this page. "
                         "One manual look at the page structure will finish the "
                         "calibration (Pass 1)."
                ),
            }
        except Exception as exc:
            return {"ok": False, "message": f"Read failed: {exc}"}

    # ---------- helpers ----------

    def _detect_login(self) -> bool:
        try:
            if LOGIN_MARKER.lower() in self.page.url.lower():
                return False
            if self.page.locator("input[type='password']").count() > 0:
                return False
            body = self.page.inner_text("body")[:8000].lower()
            return any(k in body for k in ("logout", "log out", "portfolio",
                                           "holdings", "account", "watchlist"))
        except Exception:
            return False

    def _try_navigate_to_portfolio(self) -> bool:
        for text in ("Portfolio", "Holdings", "My Portfolio", "Accounts"):
            try:
                link = self.page.get_by_text(text, exact=False).first
                if link.count() > 0:
                    link.click(timeout=4000)
                    self.page.wait_for_load_state("domcontentloaded", timeout=10000)
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

    def _extract_holdings(self) -> List[Dict]:
        holdings: List[Dict] = []
        try:
            rows = self.page.locator("table tr")
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
                        cleaned = (t.replace("R", "").replace(",", "")
                                   .replace(" ", "").strip())
                        try:
                            numbers.append(float(cleaned))
                        except ValueError:
                            numbers.append(None)
                    holdings.append({"ticker": code, "raw": texts, "numbers": numbers})
        except Exception:
            pass
        return holdings


def main():
    worker = Worker()
    log("ost_browser worker ready")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"ok": False, "message": "bad command"}), flush=True)
            continue

        cmd = req.get("cmd")
        if cmd == "open":
            resp = worker.open()
        elif cmd == "status":
            resp = worker.status()
        elif cmd == "read":
            resp = worker.read()
        elif cmd == "prepare_order":
            resp = worker.prepare_order(
                ticker=req.get("ticker", ""),
                action=req.get("action", ""),
                quantity=int(req.get("quantity", 0) or 0),
            )
        elif cmd == "close":
            resp = worker.close()
            print(json.dumps(resp), flush=True)
            break
        else:
            resp = {"ok": False, "message": f"unknown command: {cmd}"}
        print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
