import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from datetime import timedelta
from hr11_research import run_research,write_report
from intraday_instruments import InstrumentRegistry
from intraday_evaluation import EvaluationPolicy
from test_hr11_data import bar,T
from test_hr11_costs import INSTRUMENT,SCHEDULE
from intraday_sessions import SessionWindow
class ReportingTests(unittest.TestCase):
    def test_empty_universe_is_honest_and_json_safe(self):
        result=run_research(cutoff=T)
        self.assertEqual(len(result['cells']),180);self.assertEqual(result['input_record_count'],0)
        self.assertTrue(all(c['admission_state']=='INSUFFICIENT_EVIDENCE' for c in result['cells']))
        self.assertEqual(result['trades'],[])
        with tempfile.TemporaryDirectory() as tmp:
            write_report(result,tmp)
            parsed=json.loads((Path(tmp)/'report.json').read_text())
            self.assertEqual(parsed['cells'][0]['metrics']['mean_net_return'],None)
            self.assertEqual((Path(tmp)/'trades.jsonl').read_text(),'')
    def test_pipeline_with_test_only_inputs_and_missing_context(self):
        bars=[bar(i) for i in range(42)]
        session=SessionWindow('s1','2026-01-05',T,T+timedelta(hours=4),'fixture')
        result=run_research(bars,{'SOL_CASH':[session]},{'SOL_CASH':SCHEDULE},InstrumentRegistry([INSTRUMENT]),
            bars[-1].event_time,timeframes=('5m',),horizon_ids=('intraday_30m',),policy=EvaluationPolicy(units=10))
        self.assertEqual(len(result['cells']),1);self.assertGreater(len(result['decisions']),0)
        self.assertEqual(result['trades'],[])
        self.assertIn('USDZAR',result['cells'][0]['unavailable_cross_asset'])
        self.assertIn('context:MISSING_ASOF_FACTORS',result['decisions'][-1]['reasons'])
        with tempfile.TemporaryDirectory() as tmp:write_report(result,tmp)
    def test_unknown_currency_and_horizon_rejected(self):
        with self.assertRaises(ValueError):run_research(horizon_ids=('daily_1',),cutoff=T)
        with self.assertRaises(ValueError):run_research([bar(0,currency='USD')],cutoff=bar(0).event_time)
    def test_connected_fixture_runs_features_gates_trades_and_reports(self):
        from intraday_instruments import DEFAULT_REGISTRY
        instruments=[INSTRUMENT]+[DEFAULT_REGISTRY.get(name) for name in ('USDZAR_PROXY','BRENT_PROXY','JSE_INDEX_PROXY')]
        source_bars=[bar(i) for i in range(48)]
        bars=[replace(b,instrument_id=inst.instrument_id,currency=inst.currency) for inst in instruments for b in source_bars]
        session=SessionWindow('s1','2026-01-05',T,T+timedelta(hours=4),'fixture')
        result=run_research(bars,{i.instrument_id:[session] for i in instruments},{'SOL_CASH':SCHEDULE},InstrumentRegistry(instruments),
            source_bars[-1].event_time,timeframes=('5m',),horizon_ids=('intraday_30m',),policy=EvaluationPolicy(units=10,score_threshold=.1))
        self.assertGreater(len(result['trades']),0)
        self.assertTrue(all(t['cell'][0]=='SOL_CASH' for t in result['trades']))
        self.assertTrue(all(c['admission_state']=='INSUFFICIENT_EVIDENCE' for c in result['cells']))
        self.assertTrue(any(d['cross_asset_lineage'] for d in result['decisions']))
        with tempfile.TemporaryDirectory() as tmp:write_report(result,tmp)
