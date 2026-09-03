import tempfile
import unittest
from pathlib import Path

from research_indicators import DataCapabilities, MarketBar
from technical_feature_registry import DEFAULT_TECHNICAL_REGISTRY, write_registry


class TechnicalFeatureRegistryTests(unittest.TestCase):
    def test_metadata_contract_is_complete_and_unique(self):
        definitions = DEFAULT_TECHNICAL_REGISTRY.definitions()
        self.assertEqual(len(definitions), len({item.name for item in definitions}))
        self.assertTrue({"trend", "momentum", "volatility", "volume_flow", "structure", "fibonacci", "candlestick"}.issubset({item.family for item in definitions}))
        for item in definitions:
            self.assertTrue(item.required_inputs and item.output_fields and item.version)
            self.assertGreaterEqual(item.minimum_warmup, 1)

    def test_existing_calculator_keeps_capability_gate(self):
        bars = [MarketBar(close=100 + index) for index in range(30)]
        result = DEFAULT_TECHNICAL_REGISTRY.compute("atr", bars, DataCapabilities(), 29)
        self.assertFalse(result.available)
        self.assertIn("OHLC", result.reason)

    def test_planned_feature_does_not_masquerade_as_implemented(self):
        bars = [MarketBar(close=100 + index) for index in range(30)]
        result = DEFAULT_TECHNICAL_REGISTRY.compute("fibonacci_context", bars, DataCapabilities(), 29)
        self.assertFalse(result.available)
        self.assertIn("planned", result.reason)

    def test_registry_is_machine_serializable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "registry.json"
            write_registry(path)
            self.assertIn('"registry_version"', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
