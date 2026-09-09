import unittest
from dataclasses import FrozenInstanceError, replace

from domain.registry.instrument import (DEFAULT_INSTRUMENT_REGISTRY,
                                         GovernanceState, discovery_mapping)
from instrument_registry import resolve_instrument
from intraday_instruments import DEFAULT_REGISTRY as HR11_REGISTRY
from jse_adapter import JSE_TICKERS


class CanonicalInstrumentRegistryTests(unittest.TestCase):
    def test_ids_and_aliases_are_unique(self):
        items = DEFAULT_INSTRUMENT_REGISTRY.instruments()
        self.assertEqual(len({item.instrument_id for item in items}), len(items))
        self.assertEqual(DEFAULT_INSTRUMENT_REGISTRY.resolve("SASOL").instrument_id, "EQ_ZAR_SASOL")

    def test_legacy_symbols_and_data_symbols_are_preserved(self):
        for symbol, canonical in (("NPN", "EQ_ZAR_NASPERS"), ("SOL", "EQ_ZAR_SASOL"),
                                  ("BHP", "EQ_ZAR_BHP"), ("IMPJ", "EQ_ZAR_IMPLATS"),
                                  ("SHPJ", "EQ_ZAR_SHOPRITE"), ("ABSPJ", "EQ_ZAR_ABSA")):
            self.assertEqual(resolve_instrument(symbol).research_symbol, {"NPN":"NPN","SOL":"SASOL","BHP":"BHP","IMPJ":"IMPJ","SHPJ":"SHPJ","ABSPJ":"ABSPJ"}[symbol])
            item = DEFAULT_INSTRUMENT_REGISTRY.resolve(symbol)
            self.assertEqual(item.instrument_id, canonical)
            self.assertIsNone(item.execution_symbol)

    def test_hr11_enabled_instruments_reconcile_without_changing_count(self):
        self.assertEqual(len(HR11_REGISTRY.instruments(True)), 9)
        for item in HR11_REGISTRY.instruments(True):
            canonical = DEFAULT_INSTRUMENT_REGISTRY.get(item.instrument_id)
            self.assertEqual(canonical.data_symbol, item.data_symbol)

    def test_governance_and_unknown_contract_values_are_explicit(self):
        self.assertEqual(DEFAULT_INSTRUMENT_REGISTRY.get("GOLD_PROXY").governance_state, GovernanceState.RESEARCH)
        self.assertIsNone(DEFAULT_INSTRUMENT_REGISTRY.get("GOLD_PROXY").contract_multiplier)
        self.assertEqual(DEFAULT_INSTRUMENT_REGISTRY.get("PALLADIUM_PROXY").governance_state, GovernanceState.DISABLED)
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_INSTRUMENT_REGISTRY.get("EQ_ZAR_SASOL").data_symbol = "other"

    def test_contract_validation_rejects_inconsistent_tick_values(self):
        item = DEFAULT_INSTRUMENT_REGISTRY.get("EQ_ZAR_SASOL")
        with self.assertRaises(ValueError):
            replace(item, contract_multiplier=1, tick_size=1, tick_value=2)

    def test_discovery_mapping_does_not_invent_symbols(self):
        mapping = discovery_mapping(JSE_TICKERS)
        self.assertEqual(mapping["SASOL"], "EQ_ZAR_SASOL")
        self.assertIsNone(mapping["TFMJ"])
        self.assertEqual(set(mapping), set(JSE_TICKERS))

    def test_duplicate_alias_is_rejected(self):
        first = DEFAULT_INSTRUMENT_REGISTRY.get("EQ_ZAR_SASOL")
        with self.assertRaises(ValueError):
            from domain.registry.instrument import CanonicalInstrument, CanonicalInstrumentRegistry
            duplicate = replace(first, instrument_id="OTHER", aliases=("SOL",))
            CanonicalInstrumentRegistry((first, duplicate))


if __name__ == "__main__":
    unittest.main()
