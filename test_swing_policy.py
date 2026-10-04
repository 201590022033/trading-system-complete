"""Synthetic policy fixtures: causality, adverse exits, restart and no execution."""
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from domain.policy.swing_shadow import build_policy, simulate, PROFILE, digest
from application.opportunities.swing_policy import (record_and_replay, frozen_definition,
    DECISION_KIND, ENTRY_KIND, OBSERVATION_KIND, OUTCOME_KIND)
from application.opportunities.swing_technical import snapshot
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
from test_swing_technical import chart, clock
from domain.strategy import DEFAULT_STRATEGY_REGISTRY
from domain.strategy.attribution import freeze_profile
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_loop import PaperLoop
from application.opportunities.paper_host import paper_status
from dataclasses import replace


def fixture(count=86):
    signal = chart(80)
    now = clock(signal)
    features = snapshot(signal, evaluated_at=now, benchmark_chart=signal)
    # Explicit synthetic setup; never used as real strategy-performance evidence.
    features["conditions"].update(ema_uptrend=True, breakout20=True, ema20_reclaim=False,
        rsi_50_70=True, volume_above_prior20=True, outperforming_benchmark20=True, core_setup=True)
    features["values"].update(prior_low10=170, atr14_wilder=5)
    features["setup_state"] = "SHADOW_SETUP_PRESENT"
    data = chart(count)
    for index, row in enumerate(data["bars"][80:]):
        row.update(open=180, high=186, low=179, close=180+index)
    return features, data, now


class SwingPolicyTests(unittest.TestCase):
    def replay(self, data=None, horizon=3):
        features, original, now = fixture()
        data = data or original
        return simulate(build_policy(features, decision_at=now.isoformat()), data,
                        evaluated_at=clock(data).isoformat(), horizon_sessions=horizon)

    def test_time_exit_distinct_horizons_and_cost_stress(self):
        for h in (3,4,5):
            row = self.replay(horizon=h)
            self.assertEqual(row["reason"], "HORIZON_CLOSE")
            self.assertEqual(row["held_observed_sessions"], h)
            self.assertEqual(row["entry_price"], 180)
            self.assertEqual(row["target_price"], 200)
            self.assertAlmostEqual(row["net_return_scenarios"]["50"], (180+h)/180-1-.005)
            self.assertEqual(row["path_sha256"], digest(row["path"]))
            self.assertFalse(row["execution_enabled"])

    def test_gap_stop_and_negative_outcome(self):
        _, data, _ = fixture()
        data["bars"][81].update(open=168, high=169, low=167, close=168)
        row = self.replay(data)
        self.assertEqual((row["reason"], row["exit_price"]), ("GAP_STOP", 168))
        self.assertLess(row["gross_r_multiple"], -1)
        self.assertLess(row["net_return_scenarios"]["10"], 0)

    def test_ambiguous_stop_first_and_target_gap_limit(self):
        _, data, _ = fixture()
        data["bars"][81].update(open=180, high=205, low=165, close=180)
        row = self.replay(data)
        self.assertEqual(row["reason"], "AMBIGUOUS_STOP_FIRST")
        self.assertTrue(row["ambiguous_bar"])
        self.assertEqual(row["exit_price"], 170)
        data["bars"][81].update(open=205, high=207, low=165, close=180)
        row = self.replay(data)
        self.assertEqual(row["reason"], "GAP_TARGET_LIMIT")
        self.assertEqual(row["exit_price"], 200)
        self.assertFalse(row["ambiguous_bar"])

    def test_regular_stop_and_target_precede_time_exit(self):
        for prices, reason, price in ((dict(high=190,low=169), "STOP",170),
                                      (dict(high=201,low=179), "TARGET",200)):
            _, data, _ = fixture()
            data["bars"][83].update(**prices)
            row = self.replay(data)
            self.assertEqual((row["reason"],row["exit_price"]), (reason,price))

    def test_entry_bar_invalidation_and_no_pre_entry_target(self):
        _, data, _ = fixture()
        data["bars"][80]["low"] = 169
        self.assertEqual(self.replay(data)["state"], "INVALIDATED")
        data["bars"][80].update(low=179, high=220)
        self.assertEqual(self.replay(data)["reason"], "HORIZON_CLOSE")

    def test_missing_ohlc_and_truncated_or_wrong_source_fail_closed(self):
        _, data, _ = fixture()
        del data["bars"][81]["open"]
        self.assertEqual(self.replay(data)["state"], "DATA_UNAVAILABLE")
        _, data, _ = fixture()
        data["bars"] = data["bars"][80:]
        self.assertEqual(self.replay(data)["state"], "DATA_UNAVAILABLE")
        _, data, _ = fixture()
        data["symbol"] = "other"
        self.assertEqual(self.replay(data)["state"], "DATA_UNAVAILABLE")

    def test_no_lookahead_pending_entry_open_and_horizon_maturity(self):
        features, data, now = fixture()
        policy = build_policy(features, decision_at=now.isoformat())
        self.assertEqual(simulate(policy,data,evaluated_at=now.isoformat(),horizon_sessions=3)["state"],"PENDING_ENTRY")
        observed = clock(chart(82))
        before = simulate(policy,data,evaluated_at=observed.isoformat(),horizon_sessions=3)
        self.assertEqual(before["state"], "OPEN")
        for row in data["bars"][82:]:
            row.update(close=-1, high=999999)
        self.assertEqual(before,simulate(policy,data,evaluated_at=observed.isoformat(),horizon_sessions=3))

    def test_entry_expiry(self):
        features, data, now = fixture()
        data["bars"] = data["bars"][:80]+[{**data["bars"][80], "timestamp": (now+timedelta(days=9)).date().isoformat()}]
        row = simulate(build_policy(features,decision_at=now.isoformat()),data,
                       evaluated_at=clock(data).isoformat(),horizon_sessions=3)
        self.assertEqual(row["state"], "EXPIRED")

    def test_missing_no_setup_future_and_version_contracts(self):
        features, data, now = fixture()
        features["missing"] = ["VOLUME_UNAVAILABLE"]
        self.assertEqual(build_policy(features,decision_at=now.isoformat())["state"], "BLOCKED")
        features, _, _ = fixture()
        features["conditions"].update(core_setup=False,breakout20=False)
        self.assertEqual(build_policy(features,decision_at=now.isoformat())["state"], "NO_SETUP")
        with self.assertRaises(ValueError):
            build_policy(features,decision_at=(now-timedelta(days=2)).isoformat())
        features["strategy_profile_version"] = "1.0.1"
        with self.assertRaises(ValueError):
            build_policy(features,decision_at=now.isoformat())
        features, _, _ = fixture()
        policy = build_policy(features,decision_at=now.isoformat())
        with self.assertRaises(ValueError):
            simulate(policy,data,evaluated_at=now.isoformat(),horizon_sessions=2)
        policy["rules"]["trailing"] = True
        with self.assertRaises(ValueError):
            simulate(policy,data,evaluated_at=now.isoformat(),horizon_sessions=3)

    def test_both_backend_restart_idempotency_observation_freezing_and_rollback(self):
        for backend in ("sqlite","postgres-fixture"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/"state.db"
                def connect():
                    if backend == "sqlite":
                        return SQLiteRepository(path)
                    repo = PostgresRepository("postgresql://fixture",connection=SQLiteDBAPIForPostgres(path))
                    repo.initialize()
                    return repo
                repo = connect()
                try:
                    repo.create_paper_account("test", {"mode":"PAPER","cash":12345})
                    original_account = repo.paper_account("test")
                    features, data, now = fixture()
                    with repo.paper_account_transaction("test"), patch("domain.broker.paper.PaperBroker.place_order",side_effect=AssertionError("shadow must not place orders")):
                        record_and_replay(repo,"test",{"TFMJ":features},{"TFMJ":chart(80)},evaluated_at=now.isoformat(),definition=frozen_definition())
                    with repo.paper_account_transaction("test"):
                        record_and_replay(repo,"test",{}, {"TFMJ":data},evaluated_at=clock(chart(82)).isoformat(),definition=frozen_definition())
                    self.assertEqual(len(repo.paper_records("test", ENTRY_KIND,as_of=clock(data).isoformat())),1)
                    repo.close(); repo = connect()
                    # Provider revision to an already observed bar cannot replace entry/path.
                    data["bars"][80].update(open=300,high=301,low=299,close=300)
                    data["bars"][81].update(open=100,high=101,low=99,close=100)
                    with repo.paper_account_transaction("test"):
                        result = record_and_replay(repo,"test",{}, {"TFMJ":data},evaluated_at=clock(data).isoformat(),definition=frozen_definition())
                    self.assertEqual([result["horizons"][str(h)]["closed_count"] for h in (3,4,5)], [1,1,1])
                    rows = repo.paper_records("test",OUTCOME_KIND,as_of=clock(data).isoformat())
                    self.assertTrue(all(row["entry_price"]==180 and row["reason"]=="HORIZON_CLOSE" for row in rows))
                    with repo.paper_account_transaction("test"):
                        record_and_replay(repo,"test",{}, {"TFMJ":data},evaluated_at=clock(data).isoformat(),definition=frozen_definition())
                    self.assertEqual(len(repo.paper_records("test",OUTCOME_KIND,as_of=clock(data).isoformat())),3)
                    self.assertEqual(repo.paper_account("test"), original_account)
                    self.assertEqual(repo.paper_records("test","fill",as_of=clock(data).isoformat()), [])
                    self.assertEqual({row["strategy_profile_version"] for row in rows}, {"1.2.0"})
                    bad = deepcopy(frozen_definition()); bad["policy_rules"]["trailing"] = True
                    with self.assertRaises(ValueError), repo.paper_account_transaction("test"):
                        record_and_replay(repo,"test",{}, {},evaluated_at=now.isoformat(),definition=bad)
                    with self.assertRaises(RuntimeError), repo.paper_account_transaction("test"):
                        feature2 = deepcopy(features); feature2["session"] = "2026-01-01"
                        record_and_replay(repo,"test",{"TFMJ":feature2},{},evaluated_at=now.isoformat(),definition=frozen_definition())
                        raise RuntimeError("forced rollback")
                    self.assertEqual(len(repo.paper_records("test",DECISION_KIND,as_of=clock(data).isoformat())),1)
                finally:
                    repo.close()

    def test_old_frozen_jobs_and_etfs_do_not_gain_policy_attribution(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory)/"state.db")
            try:
                repo.create_paper_account("test",{"mode":"PAPER"})
                features, data, now = fixture()
                self.assertEqual(record_and_replay(repo,"test",{"TFMJ":features},{},evaluated_at=now.isoformat(),definition=None)["state"],"NOT_CONFIGURED_FOR_FROZEN_JOB")
                summary = record_and_replay(repo,"test",{"STX40":features},{},evaluated_at=now.isoformat(),definition=frozen_definition())
                self.assertEqual(summary["decision_count"],0)
                self.assertEqual(DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d").reference.strategy_profile_version,"1.0.1")
                with self.assertRaises(ValueError):
                    record_and_replay(repo,"test",{}, {},evaluated_at=now.isoformat(),definition=freeze_profile(DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d","1.1.0")))
            finally:
                repo.close()

    def test_shadow_vertical_slice_preserves_benchmark_account_rank_and_results(self):
        with tempfile.TemporaryDirectory() as directory:
            features, _, now = fixture()
            config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",))
            results, accounts, rankings = [], [], []
            for enabled in (False, True):
                repo = SQLiteRepository(Path(directory)/f"{enabled}.db")
                try:
                    loop = PaperLoop(repo,config); loop.initialize()
                    payload = {"charts":{"TFMJ":chart(80)}, "swing_technical":{"TFMJ":features}}
                    if enabled:
                        payload["swing_policy_definition"] = frozen_definition()
                    results.append(loop.cycle("same",{"job_key":"same","evaluated_at":now.isoformat(),"input":payload}))
                    accounts.append(repo.paper_account(config.account_id))
                    saved = repo.paper_record(results[-1]["ranking_record_id"])
                    shadow = saved.pop("swing_policy_shadow")
                    self.assertEqual(shadow["state"], "SHADOW_NOT_PROMOTED" if enabled else "NOT_CONFIGURED_FOR_FROZEN_JOB")
                    rankings.append(saved)
                    if enabled:
                        status = paper_status(repo,config)
                        self.assertEqual(status["swing_policy_shadow"]["strategy_profile_version"], "1.2.0")
                        self.assertEqual(status["swing_policy_shadow"]["decision_count"],1)
                finally:
                    repo.close()
            self.assertEqual(results[0],results[1])
            self.assertEqual(accounts[0],accounts[1])
            self.assertEqual(rankings[0],rankings[1])

    def test_missing_or_inserted_observed_history_never_substitutes_a_later_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory)/"history.db")
            try:
                repo.create_paper_account("test",{"mode":"PAPER"})
                features, data, now = fixture()
                with repo.paper_account_transaction("test"):
                    record_and_replay(repo,"test",{"TFMJ":features},{"TFMJ":chart(80)},evaluated_at=now.isoformat(),definition=frozen_definition())
                    record_and_replay(repo,"test",{}, {"TFMJ":data},evaluated_at=clock(chart(82)).isoformat(),definition=frozen_definition())
                for remove_entry in (True,False):
                    edited = deepcopy(data)
                    if remove_entry:
                        del edited["bars"][80]
                    else:
                        extra = deepcopy(edited["bars"][80])
                        extra["timestamp"] = (datetime.fromisoformat(extra["timestamp"])+timedelta(days=1)).date().isoformat()
                        edited["bars"].insert(81,extra)
                    with repo.paper_account_transaction("test"):
                        result = record_and_replay(repo,"test",{}, {"TFMJ":edited},evaluated_at=clock(data).isoformat(),definition=frozen_definition())
                    self.assertEqual(result["replay_states"]["DATA_UNAVAILABLE"],3)
                    self.assertEqual(repo.paper_records("test",OUTCOME_KIND,as_of=clock(data).isoformat()),[])
                with repo.paper_account_transaction("test"):
                    result = record_and_replay(repo,"test",{}, {"TFMJ":data},evaluated_at=clock(data).isoformat(),definition=frozen_definition())
                self.assertEqual(result["horizons"]["5"]["closed_count"],1)
            finally:
                repo.close()
