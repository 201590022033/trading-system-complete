"""Version isolation, legacy coexistence and transactional paper lineage."""
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from domain.strategy import DEFAULT_STRATEGY_REGISTRY, StrategyProfileRef
from domain.strategy.attribution import (StrategyAttributed, fields, reference, freeze_profile,
                                         validate_frozen_profile, same_strategy)
from domain.evaluation.effectiveness import ContextualEffectivenessLearner, EffectivenessConfig, FeatureOutcome
from domain.evaluation.opportunity import rank_opportunities
from domain.policy.engine import PolicyContext, TradePolicyEngine
from application.opportunities.public_research import candidate_from_chart
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_loop import PaperLoop, paper_feature_outcomes
from application.opportunities.paper_host import compose_paper_worker, paper_status
from application.opportunities.daily_learning import candidate_panel_summary
from application.opportunities.service import serialize_opportunity, OpportunityService
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
from test_paper_closed_loop import T, charts, frozen

PROFILE = DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d", "1.0.1")
REF = PROFILE.reference
OTHER = StrategyProfileRef("jse_swing_3_5d", "2.0.0")


def attributed_frozen(i, profile=PROFILE, **kwargs):
    return {**frozen(i, **kwargs), **freeze_profile(profile)}


class StrategyAttributionTests(unittest.TestCase):
    def test_partial_empty_and_mutable_references_fail_closed(self):
        self.assertIsNone(reference({}))
        self.assertEqual(fields(StrategyAttributed()), {})
        for values in ({"strategy_profile_id": "jse_swing_3_5d"},
                       {"strategy_profile_version": "1.0.1"},
                       {"strategy_profile_id": "", "strategy_profile_version": "1.0.1"}):
            with self.assertRaises(ValueError):
                StrategyAttributed(**values)
        with self.assertRaises(ValueError):
            same_strategy(REF, OTHER)
        with self.assertRaises(ValueError):
            same_strategy(REF, None)

    def test_frozen_definition_checksum_and_exact_versions(self):
        data = freeze_profile(PROFILE)
        self.assertEqual(validate_frozen_profile(data), REF)
        data["strategy_profile_snapshot"]["display_name"] = "hindsight replacement"
        with self.assertRaises(ValueError):
            validate_frozen_profile(data)
        old = DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d", "1.0.0")
        self.assertNotEqual(freeze_profile(old)["strategy_profile_sha256"], freeze_profile(PROFILE)["strategy_profile_sha256"])
        self.assertFalse(old.to_dict()["validated_strategy"])

    def test_learner_global_fallback_never_crosses_strategy_version_or_horizon(self):
        def row(i, ref, horizon="3_sessions", net=-.02, instrument="OTHER"):
            return FeatureOutcome("setup", "v1", "strategy", instrument, horizon, None, None,
                1, T-timedelta(days=4), T-timedelta(days=4), T-timedelta(days=1), net, net,
                str(i), **fields(ref))
        pool = [row(0, REF), row(1, OTHER, net=.9), row(2, None, net=.9),
                row(3, REF, horizon="1d", net=.9), row(4, REF, horizon="5_sessions", net=.9),
                replace(row(5, REF, net=.9), outcome_maturity=T+timedelta(days=1))]
        learner = ContextualEffectivenessLearner(EffectivenessConfig(minimum_sample=2))
        result = learner.estimate(pool, feature_id="setup", evaluated_at=T, instrument_id="MISSING",
                                  horizon_id="3_sessions", strategy_profile=REF)
        self.assertEqual(result.lineage, ("0",))
        self.assertEqual(result.fallback_level, "global")
        self.assertEqual(result.negative_outcomes, 1)
        self.assertEqual(result.status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(reference(result), REF)
        legacy = learner.estimate(pool, feature_id="setup", evaluated_at=T, horizon_id="3_sessions")
        self.assertEqual(legacy.lineage, ("2",))
        with self.assertRaises(ValueError):
            learner.estimate(pool, feature_id="setup", evaluated_at=T, strategy_profile=REF)

    def test_attribution_changes_identity_not_ranking_mathematics(self):
        chart = charts(T)["TFMJ"]
        legacy = candidate_from_chart("TFMJ", chart, evaluated_at=T, swing_history={})
        current = candidate_from_chart("TFMJ", chart, evaluated_at=T, swing_history={}, strategy_profile=REF)
        revised = candidate_from_chart("TFMJ", chart, evaluated_at=T, swing_history={}, strategy_profile=OTHER)
        results = [rank_opportunities((candidate,), evaluated_at=T) for candidate in (legacy, current, revised)]
        opportunities = [result.opportunities[0] for result in results]
        self.assertEqual(len({o.opportunity_id for o in opportunities}), 3)
        self.assertEqual(opportunities[0].ranking_score, opportunities[1].ranking_score)
        self.assertEqual(opportunities[0].ranking_components, opportunities[1].ranking_components)
        self.assertEqual(reference(results[1]), REF)
        self.assertEqual(serialize_opportunity(opportunities[0])["strategy_attribution_state"], "LEGACY_UNATTRIBUTED")
        self.assertEqual(reference(serialize_opportunity(opportunities[1])), REF)
        with self.assertRaises(ValueError):
            rank_opportunities((current, revised), evaluated_at=T)
        with self.assertRaises(ValueError):
            replace(current, **fields(OTHER))  # effectiveness lineage remains REF
        context = PolicyContext(T, T+timedelta(days=3), 86400, **fields(REF))
        policy = TradePolicyEngine().create(opportunities[1], created_at=T, context=context)
        self.assertEqual(reference(policy), REF)
        with self.assertRaises(ValueError):
            TradePolicyEngine().create(opportunities[1], created_at=T, context=replace(context, **fields(OTHER)))
        with self.assertRaises(ValueError):
            OpportunityService((opportunities[1],), (replace(policy, **fields(OTHER)),))

    def test_durable_chain_recovery_rollback_and_exact_learning_both_adapters(self):
        for backend in ("sqlite", "postgresql"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/"attributed.db"
                def open_repo():
                    if backend == "sqlite":
                        return SQLiteRepository(path)
                    repo = PostgresRepository("postgresql://fixture", connection=SQLiteDBAPIForPostgres(path))
                    repo.initialize()
                    return repo
                repo = open_repo()
                config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",), holding_sessions=1)
                try:
                    repo.save_strategy_definition(freeze_profile(PROFILE))
                    repo.save_strategy_definition(freeze_profile(PROFILE))
                    altered = replace(PROFILE, display_name="changed without new version")
                    with self.assertRaises(ValueError):
                        repo.save_strategy_definition(freeze_profile(altered))
                    loop = PaperLoop(repo, config)
                    loop.initialize()
                    loop.cycle("j0", attributed_frozen(0))
                    before = repo.paper_account(config.account_id)
                    save = repo.save_paper_record
                    def fail(rid, account, kind, at, payload):
                        if kind == "ranking":
                            raise RuntimeError("rollback injection")
                        return save(rid, account, kind, at, payload)
                    with patch.object(repo, "save_paper_record", side_effect=fail), self.assertRaises(RuntimeError):
                        loop.cycle("j1", attributed_frozen(1))
                    self.assertEqual(repo.paper_account(config.account_id), before)
                    self.assertEqual(repo.paper_records(config.account_id, "fill", as_of=(T+timedelta(days=1)).isoformat()), [])
                    result = loop.cycle("j1", attributed_frozen(1))
                    self.assertTrue(result["opened"])
                    state = repo.paper_account(config.account_id)
                    for kind in ("policy", "risk", "intent", "fill", "candidate-decision", "ranking"):
                        rows = repo.paper_records(config.account_id, kind, as_of=(T+timedelta(days=1)).isoformat())
                        self.assertTrue(rows, kind)
                        self.assertTrue(all(reference(row) == REF for row in rows), kind)
                    self.assertEqual(reference(state["broker"]["positions"][0]), REF)
                    self.assertEqual(reference(next(iter(state["book"].values()))), REF)
                    self.assertEqual(state["config"], config.to_dict())
                    repo.close()
                    repo = open_repo()
                    loop = PaperLoop(repo, config)
                    loop.initialize()
                    self.assertEqual(loop.cycle("j1", attributed_frozen(1)), result)
                    closed = loop.cycle("j2", attributed_frozen(2))
                    self.assertTrue(closed["closed"])
                    now = T+timedelta(days=3)
                    outcomes = paper_feature_outcomes(repo, config.account_id, now, strategy_profile=REF)
                    self.assertEqual(len(outcomes), 1)
                    self.assertEqual(reference(outcomes[0]), REF)
                    self.assertEqual(paper_feature_outcomes(repo, config.account_id, now), ())
                    self.assertEqual(paper_feature_outcomes(repo, config.account_id, now, strategy_profile=OTHER), ())
                    status = paper_status(repo, config)
                    self.assertEqual(reference(status["strategy_learning"]), REF)
                    self.assertEqual(status["strategy_learning"]["eligible_closed_outcomes"], 1)
                    self.assertEqual(status["strategy_learning"]["cells"][0]["status"], "INSUFFICIENT_EVIDENCE")
                    count = repo._job_sql("SELECT COUNT(*) FROM strategy_record_refs", rows=True)[0][0]
                    self.assertGreater(count, 10)
                finally:
                    repo.close()

    def test_upgrade_keeps_legacy_position_cash_config_and_outcome_unattributed(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = SQLiteRepository(Path(folder)/"legacy.db")
            config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",), holding_sessions=1)
            try:
                loop = PaperLoop(repo, config)
                loop.initialize()
                loop.cycle("j0", frozen(0))
                loop.cycle("j1", frozen(1))
                before = repo.paper_account(config.account_id)
                repo.save_strategy_definition(freeze_profile(PROFILE))
                loop.initialize()
                self.assertEqual(before, repo.paper_account(config.account_id))
                result = loop.cycle("j2", attributed_frozen(2))
                self.assertTrue(result["closed"])
                outcome = repo.paper_records(config.account_id, "outcome", as_of=(T+timedelta(days=3)).isoformat())[0]
                self.assertIsNone(reference(outcome))
                self.assertEqual(paper_feature_outcomes(repo, config.account_id, T+timedelta(days=3), strategy_profile=REF), ())
                self.assertEqual(reference(repo.paper_record(result["ranking_record_id"])), REF)
                self.assertEqual(paper_status(repo, config)["strategy_learning"]["eligible_closed_outcomes"], 0)
            finally:
                repo.close()

    def test_scheduler_pins_before_fetch_and_retry_uses_stored_definition(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = SQLiteRepository(Path(folder)/"worker.db")
            config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",))
            class Fetcher:
                calls = 0
                def get_chart(self, symbol, period):
                    self.calls += 1
                    if symbol == "TFG.JO":
                        return charts(T)["TFMJ"]
                    raise ValueError("no ETF fixture")
            fetcher = Fetcher()
            try:
                scheduler, handler = compose_paper_worker(repo, config, fetcher=fetcher, clock=lambda:T.isoformat())
                job = scheduler.enqueue(T.isoformat())
                self.assertEqual(fetcher.calls, 0)
                self.assertEqual(reference(job.checkpoint), REF)
                self.assertNotIn("strategy_profile_snapshot", job.checkpoint)
                result = handler(job)
                fetched = fetcher.calls
                self.assertEqual(handler(job), result)
                self.assertEqual(fetcher.calls, fetched)
                self.assertEqual(reference(repo.paper_record(result["ranking_record_id"])), REF)
                wrong = replace(job, checkpoint={**job.checkpoint, "strategy_profile_sha256": "0"*64})
                with self.assertRaises(ValueError):
                    handler(wrong)
            finally:
                repo.close()

    def test_legacy_scheduled_and_frozen_job_is_not_relabelled(self):
        from workers.paper_loop import PaperScheduler, FrozenPaperHandler
        with tempfile.TemporaryDirectory() as folder:
            repo = SQLiteRepository(Path(folder)/"jobs.db")
            try:
                repo.create_paper_account("a", {"mode": "PAPER"})
                legacy = PaperScheduler(repo, "a").enqueue(T.isoformat())
                current = PaperScheduler(repo, "a", strategy_profile=PROFILE).enqueue(T.isoformat())
                self.assertEqual(legacy, current)
                handler = FrozenPaperHandler(repo, "a", lambda:{"charts":{}}, lambda key, frozen:frozen, lambda:T.isoformat())
                data = handler(current)
                self.assertIsNone(reference(data))
                self.assertLess(len(json.dumps(data)), 2000)
            finally:
                repo.close()

    def test_archives_and_durable_parent_guards_retain_exact_attribution(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = SQLiteRepository(Path(folder)/"archives.db")
            try:
                repo.create_paper_account("a", {"mode": "PAPER", "ranking_record_id": None})
                repo.save_strategy_definition(freeze_profile(PROFILE))
                payload = {**fields(REF), "opportunities": [], "padding": [100]*1000}
                repo.save_paper_record("old", "a", "ranking", T.isoformat(), payload)
                self.assertEqual(repo.archive_paper_inputs("a", before=(T+timedelta(days=1)).isoformat()), 1)
                self.assertEqual(repo.paper_record("old"), payload)
                repo.save_paper_record("old", "a", "ranking", T.isoformat(), payload)
                self.assertEqual(repo._job_sql("SELECT strategy_profile_version FROM strategy_record_refs WHERE record_id='old'", rows=True)[0][0], "1.0.1")
                with self.assertRaises(ValueError):
                    repo.save_paper_record("bad", "a", "ranking", T.isoformat(),
                        {**fields(REF), "opportunities": [{**fields(OTHER)}]})
                with self.assertRaises(ValueError):
                    repo.save_paper_record("bad", "a", "candidate-outcome", T.isoformat(),
                        {**fields(REF), "decision_id": "missing"})
                repo.save_paper_record("decision", "a", "candidate-decision", T.isoformat(), fields(REF))
                with self.assertRaises(ValueError):
                    repo.save_paper_record("legacy-relabel", "a", "candidate-outcome", T.isoformat(), {"decision_id": "decision"})
                self.assertIsNone(repo.paper_record("bad"))
                with self.assertRaises(ValueError):
                    repo.save_paper_record("partial", "a", "ranking", T.isoformat(), {"strategy_profile_id": REF.strategy_profile_id})
                self.assertIsNone(repo.paper_record("partial"))
            finally:
                repo.close()

    def test_candidate_comparisons_do_not_pool_versions_or_horizons(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = SQLiteRepository(Path(folder)/"panels.db")
            try:
                repo.create_paper_account("a", {"mode": "PAPER"})
                repo.save_strategy_definition(freeze_profile(PROFILE))
                for i, ref, horizon in ((0, REF, 3), (1, None, 3), (2, REF, 5)):
                    for selected in (True, False):
                        rid = f"panel-{i}-{selected}"
                        decision = "decision-"+rid
                        repo.save_paper_record(decision, "a", "candidate-decision", T.isoformat(), fields(ref))
                        payload = {**fields(ref), "decision_id": decision, "version": "daily-candidate-panel-v1",
                            "signal_bar_at": T.isoformat(), "entry_bar_at": (T+timedelta(days=1)).isoformat(),
                            "exit_bar_at": (T+timedelta(days=4)).isoformat(), "selected": selected,
                            "horizon_sessions": horizon, "net_return": .01 if selected else -.01}
                        repo.save_paper_record(rid, "a", "candidate-outcome", T.isoformat(), payload)
                for ref, horizon in ((REF, 3), (None, 3), (REF, 5)):
                    result = candidate_panel_summary(repo, "a", evaluated_at=T+timedelta(days=5),
                                                     strategy_profile=ref, horizon_sessions=horizon)
                    self.assertEqual(result["outcome_count"], 2)
                    self.assertEqual(result["nonoverlapping_paired_sessions"], 1)
                    self.assertEqual(reference(result), ref)
            finally:
                repo.close()

    def test_metrics_targets_and_experiments_require_the_same_exact_version(self):
        from domain.evaluation.metrics import expectancy
        from domain.strategy.target_binding import StrategyTargetBinding
        from domain.evaluation.target import assess_target
        from test_strategy_target import StrategyTargetTests
        target_fixture = StrategyTargetTests()
        target_fixture.setUp()
        context = replace(target_fixture.trade_net, horizon_id="3_sessions", **fields(REF))
        criterion = target_fixture.criterion(context=context, threshold=None)
        target = replace(target_fixture.target(family=PROFILE.strategy_family, horizon=("3_sessions",)),
                         criteria=(criterion,), instrument_scope=PROFILE.universe_scope, **fields(REF))
        binding = StrategyTargetBinding.create(PROFILE, target)
        self.assertEqual(reference(binding), REF)
        self.assertEqual(assess_target(target, ()).status, "NOT_CONFIGURED")
        observation = replace(target_fixture.observation(target_fixture.criterion(), -.01), context=context, **fields(REF))
        self.assertEqual(reference(assess_target(target, (observation,))), REF)
        with self.assertRaises(ValueError):
            assess_target(target, (replace(observation, context=replace(context, **fields(OTHER)), **fields(OTHER)),))
        metric = expectancy((.01, -.02), context)
        self.assertEqual(reference(metric.to_dict()), REF)
        with self.assertRaises(ValueError):
            replace(metric, **fields(OTHER))
        from test_experiment_registry import ExperimentRegistryTests
        from domain.evaluation.experiment import InMemoryExperimentRepository
        exp = ExperimentRegistryTests()
        exp.setUp()
        definition, run = replace(exp.definition, **fields(REF)), replace(exp.run, **fields(REF))
        repo = InMemoryExperimentRepository()
        repo.register_definition(definition)
        with self.assertRaises(ValueError):
            repo.record_run(replace(run, **fields(OTHER)))
        repo.record_run(run)
        contexts = {key: replace(value, **fields(REF)) for key, value in exp.result.metric_contexts.items()}
        result = replace(exp.result, metric_contexts=contexts, **fields(REF))
        repo.record_result(result)
        self.assertEqual(reference(repo.get_experiment("e1", "v1")["results"][0]), REF)
