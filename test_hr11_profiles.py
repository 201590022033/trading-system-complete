import unittest
from dataclasses import replace
from intraday_instruments import DEFAULT_REGISTRY
from intraday_profiles import get_profile
from market_profiles import DEFAULT_PROFILE_REGISTRY
class ProfileTests(unittest.TestCase):
    def test_every_enabled_profile_is_explicit(self):
        for instrument in DEFAULT_REGISTRY.instruments(True):
            profile=get_profile(instrument)
            self.assertEqual(profile.profile_id,instrument.profile_id)
            self.assertTrue(profile.factors)
    def test_sasol_factors_and_reused_definition(self):
        p=get_profile(DEFAULT_REGISTRY.get('SOL_CASH'))
        self.assertIs(p.base_profile,DEFAULT_PROFILE_REGISTRY.get('energy_sasol'))
        self.assertEqual(p.factors,('BRENT','USDZAR','JSE_INDEX'));self.assertTrue(p.requires_volume)
    def test_unknown_never_falls_back(self):
        with self.assertRaises(KeyError):get_profile(replace(DEFAULT_REGISTRY.get('SOL_CASH'),profile_id='unknown'))
