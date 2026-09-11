import inspect, unittest
from datetime import datetime, timedelta, timezone

from domain.broker.ig_history import IGHistoricalBar, IGHistoricalSeries, IGPriceOHLC
from domain.contracts.market import CanonicalBar, DataGrade as CanonicalGrade, SourcePolicy as CanonicalSource
from domain.evaluation.experiment import InMemoryExperimentRepository
from intraday_evaluation import EvaluationPolicy
from intraday_features import VERSION as FEATURE_VERSION
from intraday_sessions import SessionWindow
from m25_hr11_validation import *

UTC=timezone.utc; START=datetime(2026,9,1,tzinfo=UTC); END=START+timedelta(days=1)

def series():
    source=CanonicalSource("IG_REST_HISTORICAL",1,"licensed",CanonicalGrade.RESEARCH,300,"RESEARCH_ONLY")
    bar=CanonicalBar("CC.D.LCO.BMU.IP","5m",START,START+timedelta(minutes=5),START+timedelta(minutes=5),75,76,74,75.5,10,75.4,75.6,source,("ig-row",))
    o=IGPriceOHLC(75,76,74,75.4); a=IGPriceOHLC(75.2,76.2,74.2,75.6); empty=IGPriceOHLC(None,None,None,None)
    wrapped=IGHistoricalBar(bar,"CC.D.LCO.BMU.IP","MINUTE_5",o,a,empty,10,None,"IG_MARKET_LOCAL_UNSPECIFIED")
    return IGHistoricalSeries("CC.D.LCO.BMU.IP","DEMO","MINUTE_5","5m",START,END,END,(wrapped,),0,2,0,7,0,False,1,9000)

class M25Tests(unittest.TestCase):
    def test_definition_is_registered_single_data_treatment(self):
        definition=experiment_definition(START,END); repo=InMemoryExperimentRepository(); repo.register_definition(definition)
        self.assertEqual(definition.changed_components,("data_source_input_availability",)); self.assertEqual(len(repo.list_experiments()),1)
    def test_baseline_and_strategy_components_are_frozen(self):
        self.assertEqual(BASELINE_COMMIT,"b080f2f0f8f7077f6861426eb4582d4c3033a149")
        for item in ("features","signal thresholds","costs","horizons","evaluation"): self.assertIn(item,FROZEN_COMPONENTS)
        self.assertEqual(EvaluationPolicy().score_threshold,.2); self.assertEqual(FEATURE_VERSION,"intraday-features-v1")
    def test_only_ig_demo_five_minute_is_accepted_and_no_yahoo_fallback(self):
        source=inspect.getsource(adapt_ig_series); self.assertNotIn("yahoo",source.lower())
        with self.assertRaises(ValueError): adapt_ig_series(object(),"BRENT_IG_CFD_USD1","USD",lambda x:None)
    def test_completed_bars_and_lineage_are_preserved(self):
        session=SessionWindow("s","2026-09-01",START,END,"UNRESOLVED_IG_SESSION_V1")
        bars=adapt_ig_series(series(),"BRENT_IG_CFD_USD1","USD",lambda x:session)
        self.assertEqual(len(bars),1); self.assertEqual(bars[0].event_time,START+timedelta(minutes=5)); self.assertEqual(bars[0].decision_time,bars[0].available_time); self.assertEqual(bars[0].input_record_ids,("ig-row",))
    def test_missing_calendar_is_invalid_not_gap_filled(self):
        with self.assertRaisesRegex(ValueError,"session calendar"): adapt_ig_series(series(),"BRENT_IG_CFD_USD1","USD",lambda x:None)
    def test_evidence_classes_keep_negative_and_insufficient_distinct(self):
        self.assertEqual(classify_evidence(valid_context=True,outcome_ready_samples=0,net_expectancy=None),"INSUFFICIENT_EVIDENCE")
        self.assertEqual(classify_evidence(valid_context=True,outcome_ready_samples=2,net_expectancy=-.01),"NEGATIVE_EVIDENCE")
        self.assertEqual(classify_evidence(valid_context=False,outcome_ready_samples=2,net_expectancy=.01),"INVALID_CONTEXT")
    def test_range_and_malformed_taxonomy_passes_through_unchanged(self):
        value=series().summary(); self.assertEqual(value["excluded_outside_range"],7); self.assertEqual(value["excluded_malformed"],0); self.assertEqual(value["gaps"],2)
    def test_unavailable_run_does_not_mislabel_zero_trades(self):
        value=unavailable_result(); self.assertEqual(value["evidence_classification"],"INSUFFICIENT_EVIDENCE"); self.assertNotIn("failure",repr(value).lower()); self.assertEqual(value["metrics"],{})
    def test_no_execution_or_runtime_dependencies(self):
        source=inspect.getsource(__import__("m25_hr11_validation"));
        for forbidden in ("PaperBroker","place_order","Yahoo","TradePolicy","RiskEngine"): self.assertNotIn(forbidden,source)

if __name__=="__main__": unittest.main()
