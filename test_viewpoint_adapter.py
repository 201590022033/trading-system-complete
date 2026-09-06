import unittest
from viewpoint_adapter import (Availability, BrokerInstrumentMapping, BrokerOrder,
    CashBalance, ViewPointAdapter)
from provider_interfaces import LiveExecutionDisabled


class ViewPointBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.adapter = ViewPointAdapter(availability=Availability.AVAILABLE)
        self.mapping = BrokerInstrumentMapping("SOL", "standard_bank_viewpoint", "VERIFIED-ID")
        self.cash = CashBalance("A", "ZAR", available=1000)

    def test_unavailable_and_unknown_cash_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError, "not_authenticated"):
            ViewPointAdapter(availability=Availability.NOT_AUTHENTICATED).get_accounts()
        with self.assertRaisesRegex(ValueError, "available cash"):
            self.adapter.prepare_order({"intent_id":"i", "account_id":"A", "instrument":"SOL",
                "side":"BUY", "quantity":1, "limit_price":10}, mapping=self.mapping, cash=CashBalance("A"))

    def test_prepare_only_and_mapping_and_duplicate_guards(self):
        order = self.adapter.prepare_order({"intent_id":"i", "account_id":"A", "instrument":"SOL",
            "side":"BUY", "quantity":2, "limit_price":10}, mapping=self.mapping, cash=self.cash)
        self.assertEqual(order.status, "PREPARED")
        with self.assertRaises(LiveExecutionDisabled): self.adapter.submit_order(order)
        with self.assertRaises(ValueError):
            self.adapter.prepare_order({"intent_id":"j", "account_id":"A", "instrument":"SOL",
                "side":"BUY", "quantity":1, "limit_price":10}, mapping=self.mapping, cash=self.cash,
                open_orders=[BrokerOrder("b", "A", "SOL", "BUY", 1, remaining_quantity=1, status="PENDING")])

    def test_reconciliation_unknown_is_not_a_fill(self):
        result = self.adapter.reconcile_order("missing")
        self.assertEqual(result.status, "UNKNOWN")
        self.assertEqual(result.filled_quantity, 0)


if __name__ == "__main__": unittest.main()
