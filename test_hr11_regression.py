"""Cross-stage invariants and the immutable daily research benchmark."""
import hashlib
import json
import unittest
from pathlib import Path
from dataclasses import replace
from datetime import timedelta
from intraday_data import SourcePolicy
from intraday_sessions import aggregate
from intraday_features import compute_features
from intraday_robustness import prepare_cell
import test_hr11_evaluation as evaluation_fixtures
import test_hr11_router as router_fixtures
from intraday_router import preview
from test_hr11_data import bar
from test_hr11_sessions import SESSION

class RegressionTests(unittest.TestCase):
    def test_immutable_daily_artifact_and_code_hashes(self):
        baseline=json.loads(Path('analysis/results/hr11/baseline.json').read_text())
        self.assertEqual(len(baseline['immutable_sha256']),39)
        for path,digest in baseline['immutable_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),digest,path)
    def test_all_timeframes_preserve_prefix_features(self):
        bars=[bar(i) for i in range(24)];cutoff=bar(11).event_time
        future=[b if i<12 else replace(b,close=b.close+100,open=b.open+100,high=b.high+100,low=b.low+100) for i,b in enumerate(bars)]
        for frame in ('5m','15m','30m','60m'):
            first=aggregate(bars,[SESSION],frame,cutoff).bars
            second=aggregate(future,[SESSION],frame,cutoff).bars
            self.assertEqual(compute_features(first,cutoff,[SESSION]),compute_features(second,cutoff,[SESSION]))
    def test_declared_break_daily_roundtrip(self):
        session=replace(SESSION,close_time=SESSION.open_time+timedelta(minutes=20),breaks=((bar(0).event_time,bar(1).event_time),))
        daily=aggregate([bar(0),bar(2),bar(3)],[session],'1d',session.close_time).bars
        self.assertEqual(len(daily),1)
        self.assertEqual(aggregate(daily,[session],'1d',session.close_time).bars,daily)
    def test_overlap_cannot_manufacture_robustness_evidence(self):
        trade=evaluation_fixtures.EvaluationTests().run_eval().trades[0]
        with self.assertRaises(ValueError):prepare_cell(trade.cell,(trade,trade))
    def test_nonfinite_freshness_and_router_score_rejected(self):
        with self.assertRaises(ValueError):replace(bar(0).source,max_age_seconds=float('nan'))
        args=router_fixtures.RouterTests().args()
        args['decision']=replace(args['decision'],score=float('nan'))
        self.assertFalse(preview(**args).accepted)
    def test_noncausal_decision_builder_rejected(self):
        def invalid(c,p,e):
            decision,gates=evaluation_fixtures.builder(c,p,e)
            return replace(decision,decision_time=decision.decision_time+timedelta(minutes=5)),gates
        with self.assertRaises(ValueError):evaluation_fixtures.EvaluationTests().run_eval(builder_=invalid)
