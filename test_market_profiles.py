"""Offline characterization tests for M4 market profiles."""

from types import SimpleNamespace
import unittest

from jse_adapter import DataSourceType
from market_profiles import DEFAULT_PROFILE_REGISTRY, MarketProfile, ProfileRegistry
from signal_pipeline import JSESignalEngine


class MarketProfileTests(unittest.TestCase):
    def test_required_sector_and_instrument_profiles_are_selectable(self):
        expected = {
            "ALSI": "index_derivative",
            "NPN": "offshore_earner",
            "ABSPJ": "banks_financials",
            "GFI": "gold_miners",
            "IMPJ": "pgm_mining",
            "BHP": "diversified_mining",
            "SASOL": "energy_sasol",
            "SHPJ": "retail_consumer",
            "AFG": "agri_linked",
            "USD/ZAR": "usdzar",
        }
        for ticker, profile_id in expected.items():
            with self.subTest(ticker=ticker):
                self.assertEqual(DEFAULT_PROFILE_REGISTRY.select(ticker).profile_id, profile_id)

    def test_unknown_ticker_uses_single_stock_fallback(self):
        profile = DEFAULT_PROFILE_REGISTRY.select("UNKNOWN")
        self.assertEqual(profile.profile_id, "single_stock")
        self.assertEqual(profile.instrument_type, "ssf_or_share_cfd")

    def test_registry_accepts_explicit_configuration(self):
        fallback = MarketProfile("single_stock", "general", "ssf_or_share_cfd")
        custom = MarketProfile("custom", "custom_sector", "custom_instrument")
        registry = ProfileRegistry((fallback, custom), {"XYZ": "custom"})
        self.assertEqual(registry.select("xyz"), custom)

    def test_profiles_preserve_legacy_macro_coefficients_and_clamp(self):
        engine = JSESignalEngine(
            tickers=["NPN"],
            price_source=DataSourceType.MOCK,
            news_source="mock",
            use_macro=False,
        )
        engine.macro_report = SimpleNamespace(
            tickers={"SASOL": {"score": 0.5}},
            macro={
                "ZAR": {"score": -0.6},
                "GOLD": {"score": 0.7},
                "OIL": {"score": 0.8},
            },
        )
        # Legacy Sasol result: .10*.5 + .05*.6 + .08*.8 = .144.
        self.assertAlmostEqual(engine._macro_adjustment("SASOL"), 0.144)
        self.assertAlmostEqual(engine._macro_adjustment("NPN"), 0.03)
        self.assertAlmostEqual(engine._macro_adjustment("GFI"), 0.056)
        self.assertAlmostEqual(engine._macro_adjustment("ABSPJ"), -0.03)

        engine.macro_report.tickers["SASOL"]["score"] = 1.0
        engine.macro_report.macro["ZAR"]["score"] = -1.0
        engine.macro_report.macro["OIL"]["score"] = 1.0
        self.assertEqual(engine._macro_adjustment("SASOL"), 0.15)


if __name__ == "__main__":
    unittest.main()
