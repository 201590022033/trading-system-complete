import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_loop import PaperLoop
from application.opportunities.paper_host import paper_status, persisted_news
from application.opportunities.paper_controls import update_controls
from application.opportunities.operator_api import create_operator_blueprint
from application.opportunities.news_ingestion import persist_news_report
from persistence.sqlite_repository import SQLiteRepository
from test_paper_closed_loop import T, frozen


class OperationalPortfolioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'state.db'
        self.repo = SQLiteRepository(self.path)
        self.config = replace(PaperLoopConfig.load('config/paper.example.json'), universe=('TFMJ',))
        self.loop = PaperLoop(self.repo, self.config)
        self.loop.initialize()

    def tearDown(self):
        self.repo.close()
        self.tmp.cleanup()

    def test_control_changes_survive_restart_and_reach_actual_risk(self):
        self.loop.cycle('j0', frozen(0))
        update_controls(self.repo, self.config, {'aggression': 'aggressive', 'paused': True}, now=T)
        restarted = PaperLoop(self.repo, self.config)
        restarted.initialize()
        paused = restarted.cycle('j1', frozen(1))
        self.assertFalse(paused['opened'])
        update_controls(self.repo, self.config, {'paused': False}, now=T+timedelta(days=1))
        opened = restarted.cycle('j2', frozen(2))
        self.assertTrue(opened['opened'])
        policies = self.repo.paper_records(self.config.account_id, 'policy', as_of=(T+timedelta(days=3)).isoformat())
        self.assertEqual(policies[0]['requested_risk_fraction'], self.config.risk_fraction)
        self.assertEqual(policies[0]['provenance']['aggression'], 'aggressive')
        self.assertEqual(len(self.repo.paper_records(self.config.account_id, 'control', as_of=(T+timedelta(days=3)).isoformat())), 2)

    def test_operator_authentication_validation_and_audit(self):
        app=Flask(__name__)
        app.secret_key='test-only'
        app.register_blueprint(create_operator_blueprint(lambda: SQLiteRepository(self.path), self.config))
        with patch.dict('os.environ', {'PAPER_CONTROL_TOKEN':'fixture-access-key'}), app.test_client() as client:
            self.assertEqual(client.post('/api/paper/controls',json={'aggression':'aggressive'}).status_code,401)
            self.assertEqual(client.post('/api/paper/session',json={'key':'wrong'}).status_code,401)
            self.assertEqual(client.post('/api/paper/session',json={'key':'fixture-access-key'}).status_code,200)
            self.assertEqual(client.post('/api/paper/controls',json={'mode':'LIVE'}).status_code,422)
            self.assertEqual(client.post('/api/paper/controls',json={'paused':'false'}).status_code,422)
            self.assertEqual(client.post('/api/paper/controls',json={'aggression':'balanced'}).status_code,200)
            self.assertEqual(client.post('/api/paper/cycle').status_code,202)
            client.delete('/api/paper/session')
            self.assertEqual(client.post('/api/paper/cycle').status_code,401)
        self.assertEqual(self.repo.paper_account(self.config.account_id)['controls']['aggression'],'balanced')

    def test_news_persistence_is_causal_deduplicated_and_keeps_ai_provenance(self):
        item={'source':'Moneyweb','timestamp':(T-timedelta(hours=2)).isoformat(),
              'headline':'TFG results','score':.4,'assets':[{'name':'TFMJ'},{'name':'ZAR'}],
              'url':'https://www.moneyweb.co.za/fixture','llm_used':True,
              'analysis_provider':'fixture-provider','analysis_model':'fixture-model'}
        self.assertEqual(persist_news_report(self.repo,{'items':[item]},observed_at=T.isoformat()),1)
        self.assertEqual(persist_news_report(self.repo,{'items':[item]},observed_at=(T+timedelta(hours=1)).isoformat()),0)
        before=persisted_news(self.repo,T-timedelta(seconds=1))
        self.assertFalse(before['items'])
        actual=persisted_news(self.repo,T)['items'][0]
        self.assertEqual(actual['available_at'],T.isoformat())
        self.assertTrue(actual['llm_used'])
        self.assertEqual(actual['analysis_model'],'fixture-model')
        revised={**item,'score':-.5}
        self.assertEqual(persist_news_report(self.repo,{'items':[revised]},observed_at=(T+timedelta(hours=1)).isoformat()),1)
        self.assertEqual(persisted_news(self.repo,T)['items'][0]['score'],.4)
        self.assertEqual(len(persisted_news(self.repo,T+timedelta(hours=1))['items']),1)
        self.assertEqual(persisted_news(self.repo,T+timedelta(hours=1))['items'][0]['score'],-.5)
        future={**item,'timestamp':(T+timedelta(days=1)).isoformat()}
        self.assertEqual(persist_news_report(self.repo,{'items':[future]},observed_at=T.isoformat()),0)

    def test_portfolio_workspace_contains_control_and_persisted_account_views(self):
        html=Path('templates/dashboard.html').read_text(encoding='utf-8')
        for identity in ('paper-aggression','paper-positions','paper-fills','paper-outcomes','paper-learning','account-status'):
            self.assertIn('id="'+identity+'"',html)
        status=paper_status(self.repo,self.config)
        self.assertEqual(status['account']['equity'],100000)
        self.assertEqual(status['learning']['eligible_outcomes'],0)
        self.assertEqual(status['controls']['aggression'],'conservative')
