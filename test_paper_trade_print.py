import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class PaperTradePrintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
        cls.dashboard_js = (ROOT / "static/js/dashboard.js").read_text(encoding="utf-8")
        cls.accounts_js = (ROOT / "static/js/accounts.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "static/css/accounts.css").read_text(encoding="utf-8")

    def test_canonical_cards_offer_print_and_manual_capture(self):
        self.assertIn("data-print-paper-trade", self.dashboard_js)
        self.assertIn("data-capture-paper-trade", self.dashboard_js)
        self.assertIn("window.print()", self.dashboard_js)
        self.assertIn('id="paper-trade-ticket"', self.html)

    def test_printout_retains_research_and_execution_boundaries(self):
        for phrase in (
            "RESEARCH-ONLY PAPER WORKSHEET",
            "not a recommendation or broker order",
            "Live execution is disabled",
            "Net P&L after all costs",
        ):
            self.assertIn(phrase, self.dashboard_js)
        self.assertIn("@media print", self.css)
        self.assertNotIn("submit_order", self.dashboard_js)

    def test_capture_prefills_existing_journal_without_inventing_execution(self):
        self.assertIn("paper-trade-prefill", self.dashboard_js)
        self.assertIn("paper-trade-prefill", self.accounts_js)
        self.assertIn("APP_INSPIRED", self.accounts_js)
        self.assertIn("actual quantity, price, time, stop, target, risk and broker reference", self.accounts_js)
        for field in ("quantity", "entry_price", "opened_at", "stop_price", "target_price", "planned_risk"):
            self.assertNotIn(f"form.elements.{field}.value=detail", self.accounts_js)

    def test_non_directional_research_cannot_prefill_trade_direction(self):
        self.assertIn("!['LONG','SHORT'].includes(item.direction)", self.dashboard_js)
        self.assertIn("!['LONG','SHORT'].includes(detail.direction)", self.accounts_js)


if __name__ == "__main__":
    unittest.main()
