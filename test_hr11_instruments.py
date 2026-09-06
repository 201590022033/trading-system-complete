import unittest
from dataclasses import FrozenInstanceError,replace
from intraday_instruments import DEFAULT_REGISTRY,InstrumentRegistry,DataGrade
from instrument_registry import resolve_instrument

class InstrumentTests(unittest.TestCase):
    def test_universe_and_underlying_separation(self):
        self.assertEqual(len(DEFAULT_REGISTRY.instruments(True)),9)
        cash=DEFAULT_REGISTRY.get('SOL_CASH')
        self.assertEqual(cash.underlying_id,resolve_instrument('SOL').research_symbol)
        self.assertNotEqual(cash.instrument_id,DEFAULT_REGISTRY.get('SASOL_CFD').instrument_id)
        self.assertFalse(DEFAULT_REGISTRY.get('SASOL_CFD').enabled)
    def test_invalid_metadata_fails(self):
        base=DEFAULT_REGISTRY.get('SOL_CASH')
        for values in ({'tick_size':-1},{'contract_multiplier':0},{'leverage':float('nan')},
                       {'tick_size':1,'tick_value':2},{'currency':'unknown'},{'data_grade':'live'}):
            with self.subTest(values=values),self.assertRaises(ValueError): replace(base,**values)
    def test_unknown_and_duplicate_identity_refused(self):
        item=DEFAULT_REGISTRY.get('SOL_CASH')
        with self.assertRaises(KeyError): DEFAULT_REGISTRY.get('UNKNOWN')
        with self.assertRaises(ValueError): InstrumentRegistry([item,item])
        with self.assertRaises(FrozenInstanceError): item.enabled=False
    def test_execution_symbol_is_not_live_authority(self):
        item=replace(DEFAULT_REGISTRY.get('SOL_CASH'),execution_symbol='SOL-live-label')
        self.assertFalse(item.to_dict()['live_execution_available'])
        self.assertEqual(item.data_grade,DataGrade.RESEARCH)
        self.assertIsNone(DEFAULT_REGISTRY.get('GOLD_PROXY').contract_multiplier)
