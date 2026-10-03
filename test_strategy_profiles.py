import unittest
from dataclasses import FrozenInstanceError, replace
from domain.strategy import (DEFAULT_STRATEGY_REGISTRY, StrategyProfileRef, StrategyProfileRegistry,
                             StrategyLifecycle, CapabilityState)


class StrategyProfileTests(unittest.TestCase):
    def test_three_profiles_have_truthful_distinct_scopes(self):
        profiles = DEFAULT_STRATEGY_REGISTRY.current_profiles()
        self.assertEqual(len(profiles), 3)
        swing, intraday, investment = profiles
        self.assertEqual(swing.lifecycle, StrategyLifecycle.ACTIVE_RESEARCH_PAPER)
        self.assertEqual(swing.intended_horizon_ids, ("3_sessions", "4_sessions", "5_sessions"))
        self.assertEqual(intraday.intended_horizon_ids[-1], "intraday_eod")
        self.assertEqual(investment.decision_timeframe, "NOT_CONFIGURED")
        self.assertEqual(swing.canonical_workflow_tab, "canonical-opportunities")
        self.assertIsNone(intraday.canonical_workflow_tab)
        self.assertIsNone(investment.canonical_workflow_tab)
        for profile in profiles:
            self.assertFalse(profile.to_dict()["validated_strategy"])
            self.assertFalse(profile.to_dict()["live_execution"])
            self.assertFalse(profile.to_dict()["strategy_execution_enabled"])
        self.assertTrue(any(c.state is CapabilityState.BLOCKED for c in intraday.capabilities))
        self.assertIn("not reused", " ".join(investment.limitations))

    def test_exact_old_version_survives_new_current_version(self):
        old = DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d", "1.0.0")
        new = replace(old, reference=StrategyProfileRef("jse_swing_3_5d", "2.0.0"),
                      display_name="Revised research definition")
        registry = StrategyProfileRegistry((old, new), current_versions={"jse_swing_3_5d": "2.0.0"})
        self.assertIs(registry.resolve("jse_swing_3_5d"), new)
        self.assertIs(registry.resolve("jse_swing_3_5d", "1.0.0"), old)
        self.assertEqual(old.display_name, "JSE Swing Trader — 3–5 Day")
        with self.assertRaises(KeyError):
            registry.resolve("jse_swing_3_5d", "9.0.0")
        with self.assertRaises(ValueError):
            StrategyProfileRegistry((old, old), current_versions={"jse_swing_3_5d": "1.0.0"})
        with self.assertRaises(ValueError):
            StrategyProfileRegistry((old,), current_versions={"jse_swing_3_5d": "2.0.0"})

    def test_profiles_and_serialized_snapshots_cannot_mutate_source(self):
        profile = DEFAULT_STRATEGY_REGISTRY.current_profiles()[0]
        with self.assertRaises(FrozenInstanceError):
            profile.display_name = "changed"
        snapshot = profile.to_dict()
        snapshot["capabilities"][0]["description"] = "changed"
        snapshot["intended_horizon_ids"].append("intraday_5m")
        self.assertNotEqual(profile.to_dict(), snapshot)

    def test_live_mode_placeholder_workflow_and_invalid_identity_fail_closed(self):
        profile = DEFAULT_STRATEGY_REGISTRY.current_profiles()[0]
        with self.assertRaises(ValueError):
            replace(profile, allowed_research_modes=("LIVE",))
        with self.assertRaises(ValueError):
            replace(profile, lifecycle=StrategyLifecycle.DEVELOPMENT)
        with self.assertRaises(ValueError):
            replace(profile, canonical_workflow_tab="broker-execution")
        for identity, version in (("", "1.0.0"), ("../bad", "1.0.0"), ("swing", "latest")):
            with self.assertRaises(ValueError):
                StrategyProfileRef(identity, version)

    def test_conflicting_capability_ids_are_rejected(self):
        profile = DEFAULT_STRATEGY_REGISTRY.current_profiles()[0]
        with self.assertRaises(ValueError):
            replace(profile, capabilities=(profile.capabilities[0],)*2)

    def test_mutable_nested_scope_and_unreferenced_implemented_capabilities_fail_closed(self):
        profile = DEFAULT_STRATEGY_REGISTRY.current_profiles()[0]
        with self.assertRaises(ValueError):
            replace(profile, universe_scope=({"mutable": "scope"},))
        with self.assertRaises(ValueError):
            replace(profile.capabilities[0], component_references=())
        with self.assertRaises(ValueError):
            replace(profile.capabilities[0], component_references=({"mutable": "reference"},))
