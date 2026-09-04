import unittest

from provider_interfaces import LiveExecutionDisabled, PaperExecutionProvider


class ProviderBoundaryTests(unittest.TestCase):
    def test_preview_is_paper_and_submit_hard_fails(self):
        provider = PaperExecutionProvider()
        preview = provider.preview_order({"instrument": "NPN", "side": "buy",
            "quantity": 2, "order_type": "limit", "estimated_price": 100})
        self.assertEqual(preview.mode, "paper")
        with self.assertRaises(LiveExecutionDisabled):
            provider.submit_order({})


if __name__ == "__main__":
    unittest.main()
