from copy import deepcopy
from datetime import datetime, timezone
import unittest
from unittest.mock import Mock
from application.opportunities.learning_overview import overview, project, REMOTE


def evidence():
    return {'swing_technical_learning': {'strategy_profile_id':'jse_swing_3_5d', 'strategy_profile_version':'1.1.0',
        'decision_count_in_read_window': 8, 'read_limit':5000,
        'horizons': {str(h): {'sample_count':n,'negative_count':1} for h,n in ((3,4),(4,3),(5,2))},
        'condition_cohorts': {'3': {'ema_uptrend_absent': {'sample_count':2,'negative_outcomes':1}}}},
        'swing_technical': {'SASOL': {'state':'PARTIAL','session':'2026-10-02','missing':['REAL_OHLC_UNAVAILABLE']}},
        'account': {'account_id':'PRIVATE_ACCOUNT','balance':123456}, 'positions':['PRIVATE_POSITION']}


class LearningOverviewTests(unittest.TestCase):
    def test_progress_keeps_negative_and_absent_controls_without_private_fields(self):
        result=project(evidence(), {}, {}, source='RAILWAY', now=datetime.now(timezone.utc))
        self.assertEqual(result['horizons']['3'], {'matured':4,'pending':4,'negative':1})
        self.assertEqual(result['horizons']['5']['pending'],6)
        self.assertEqual(result['condition_cohorts']['3'][0]['condition'],'ema_uptrend_absent')
        self.assertEqual(result['sasol']['missing'],['REAL_OHLC_UNAVAILABLE'])
        self.assertNotIn('PRIVATE',str(result))
        self.assertFalse(result['real_data_backtest_admitted'])
        self.assertFalse(result['automatic_promotion'])

    def test_unconfigured_counts_are_unavailable_not_zero(self):
        result=project({'state':'NOT_CONFIGURED'}, {}, {}, source='LOCAL', now=datetime.now(timezone.utc))
        self.assertIsNone(result['decisions_in_read_window'])
        self.assertIsNone(result['horizons']['3']['matured'])

    def test_bad_denominators_booleans_and_counters_are_refused(self):
        for bad in (True,-1,1000001,2):
            paper=evidence(); paper['swing_technical_learning']['decision_count_in_read_window']=bad
            with self.assertRaises(ValueError): project(paper,{}, {}, source='LOCAL',now=datetime.now(timezone.utc))

    def test_remote_pinned_read_only_projection_does_not_open_local_database(self):
        factory=Mock(side_effect=AssertionError('no local database'))
        reader=Mock(side_effect=[{'database_backend':'postgresql','database_state':'AVAILABLE'},evidence(),{}])
        result=overview(factory,{'SWING_LEARNING_SOURCE':'RAILWAY','SWING_RESEARCH_URL':REMOTE},reader)
        self.assertEqual(result['runtime'],'RAILWAY'); self.assertEqual(result['state'],'AVAILABLE')
        self.assertEqual([c.args[0] for c in reader.call_args_list],['/api/learning/status','/api/paper/status','/api/v1/swing-research/status'])
        factory.assert_not_called()

    def test_wrong_url_failure_or_wrong_backend_never_falls_back_to_zero_local_counts(self):
        for url,reader in ((REMOTE+'?secret',Mock()),(REMOTE,Mock(side_effect=RuntimeError('PRIVATE_TOKEN'))),
                           (REMOTE,Mock(side_effect=[{'database_backend':'sqlite'},evidence(),{}]))):
            factory=Mock()
            result=overview(factory,{'SWING_LEARNING_SOURCE':'RAILWAY','SWING_RESEARCH_URL':url},reader)
            self.assertEqual(result['state'],'UNAVAILABLE');self.assertEqual(result['runtime'],'RAILWAY')
            self.assertNotIn('PRIVATE',str(result)); factory.assert_not_called()

    def test_hosted_runtime_does_not_recursively_read_itself(self):
        factory,reader=Mock(side_effect=RuntimeError('database missing')),Mock()
        result=overview(factory,{'SWING_LEARNING_SOURCE':'RAILWAY','SWING_RESEARCH_URL':REMOTE,'RAILWAY_ENVIRONMENT_ID':'hosted'},reader)
        self.assertEqual(result['runtime'],'LOCAL');reader.assert_not_called()


if __name__=='__main__': unittest.main()
