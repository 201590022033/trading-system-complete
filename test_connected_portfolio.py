import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from connected_accounts import aggregate
from connected_portfolio_api import create_connected_blueprint
from manual_demo_journal import ManualDemoJournal, PREFIX
from persistence.sqlite_repository import SQLiteRepository

T = datetime(2026, 9, 20, 10, tzinfo=timezone.utc)
ID = 'c5d9efdf-f7c6-4f60-bfc4-d830fb73de4e'


def account(**overrides):
    return dict(broker='IG', environment='DEMO', account_id='fixture-1',
                available_funds=20100, balance=20100, account_currency='USD',
                retrieved_at=T.isoformat(), freshness='FRESH', **overrides)


def snapshot():
    return aggregate([account()], {'USD': {'zar_per_unit': 17, 'as_of': (T-timedelta(days=2)).isoformat(), 'source': 'fixture'}}, now=T)


def entry(**overrides):
    result = dict(trade_id=ID, instrument='fixture-EPIC', direction='LONG',
                  quantity=2, entry_price=100, opened_at=(T-timedelta(hours=1)).isoformat(),
                  idea_source='MY_IDEA', planned_risk=50, notes='Own thesis')
    result.update(overrides)
    return result


class ConnectedCashTests(unittest.TestCase):
    def test_totals_separate_environment_and_do_not_include_simulator(self):
        second = {**account(), 'broker': 'Standard Bank', 'account_currency': 'ZAR', 'available_funds': 5000}
        real = {**second, 'environment': 'LIVE', 'available_funds': 6000}
        result = aggregate([account(), second, real], {'USD': {'zar_per_unit': 17, 'as_of': T.isoformat()}}, now=T)
        self.assertEqual(result['groups']['DEMO']['zar_total'], 346700)
        self.assertEqual(result['groups']['LIVE']['zar_total'], 6000)
        self.assertNotIn('starting_cash', str(result))

    def test_missing_fx_preserves_usd_but_never_guesses_total(self):
        result = aggregate([account()], {}, now=T)
        self.assertIsNone(result['groups']['DEMO']['zar_total'])
        self.assertEqual(result['groups']['DEMO']['by_currency'], {'USD': 20100})
        self.assertEqual(result['accounts'][0]['state'], 'AVAILABLE')

    def test_missing_stale_future_and_nonfinite_evidence_excluded(self):
        for changed in ({'available_funds': None}, {'available_funds': float('nan')},
                        {'retrieved_at': (T-timedelta(minutes=6)).isoformat()},
                        {'retrieved_at': (T+timedelta(seconds=1)).isoformat()}):
            result = aggregate([{**account(), **changed}], {}, now=T)
            self.assertFalse(result['groups']['DEMO']['complete'])
            self.assertEqual(result['groups']['DEMO']['by_currency'], {})
        for at in (T-timedelta(days=5), T+timedelta(seconds=1)):
            self.assertIsNone(aggregate([account()], {'USD': {'zar_per_unit': 17, 'as_of': at.isoformat()}}, now=T)['groups']['DEMO']['zar_total'])

    def test_duplicates_fail_instead_of_double_count(self):
        with self.assertRaises(ValueError):
            aggregate([account(), account()], {}, now=T)


class ManualJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'ledger.db'
        self.repo = SQLiteRepository(self.path)
        self.account = snapshot()['accounts'][0]
        self.key = self.account['key']
        self.journal = ManualDemoJournal(self.repo, clock=lambda: T)

    def tearDown(self):
        self.repo.close()
        self.temp.cleanup()

    def test_restart_idempotency_and_no_cash_or_canonical_mutation(self):
        first = self.journal.open(self.account, entry())
        self.assertEqual(self.journal.open(self.account, entry()), first)
        with self.assertRaises(ValueError):
            self.journal.open(self.account, entry(quantity=3))
        body = dict(closed_at=T.isoformat(), exit_price=90, net_pnl=-60)
        closed = self.journal.close(self.key, ID, body)
        self.assertEqual(self.journal.close(self.key, ID, body), closed)
        with self.assertRaises(ValueError):
            self.journal.close(self.key, ID, {**body, 'net_pnl': 4})
        self.repo.close()
        self.repo = SQLiteRepository(self.path)
        review = ManualDemoJournal(self.repo, clock=lambda: T).review(self.key)
        self.assertEqual(review['closed_count'], 1)
        self.assertEqual(review['trades'][0]['r_multiple'], -1.2)
        self.assertEqual(review['trades'][0]['outcome'], 'LOSS')
        self.assertTrue(any('exceeded' in note for note in review['trades'][0]['assessment']))
        self.assertEqual(review['patterns'][0]['net_pnl'], -60)
        self.assertEqual(review['patterns'][0]['idea_source'], 'MY_IDEA')
        saved = self.repo.paper_account(PREFIX+self.key)
        self.assertEqual(saved['account']['available_funds'], 20100)
        for kind in ('outcome', 'fill', 'ranking', 'policy'):
            self.assertEqual(self.repo.paper_records(PREFIX+self.key, kind, as_of=T.isoformat()), [])

    def test_causal_availability_not_backdated_to_occurrence(self):
        self.journal.open(self.account, entry())
        self.assertFalse(self.journal.review(self.key, as_of=T-timedelta(seconds=1))['trades'])
        later = ManualDemoJournal(self.repo, clock=lambda: T+timedelta(days=1))
        later.close(self.key, ID, dict(closed_at=T.isoformat(), exit_price=110, net_pnl=10))
        self.assertEqual(later.review(self.key, as_of=T)['closed_count'], 0)
        self.assertEqual(later.review(self.key)['closed_count'], 1)

    def test_validation_and_cross_account_isolation(self):
        for fields in ({'quantity': -1}, {'quantity': True}, {'entry_price': float('inf')},
                       {'opened_at': '2026-09-20T10:00:00'}, {'opened_at': (T+timedelta(days=1)).isoformat()},
                       {'idea_source': 'CANONICAL_VERIFIED'}, {'notes': 'x'*2001}):
            with self.assertRaises(ValueError):
                self.journal.open(self.account, entry(**fields))
        with self.assertRaises(ValueError):
            self.journal.open({**self.account, 'environment': 'LIVE'}, entry())
        self.journal.open(self.account, entry())
        self.assertFalse(self.journal.review('f'*24)['trades'])
        with self.assertRaises(ValueError):
            self.journal.close('f'*24, ID, dict(closed_at=T.isoformat(), exit_price=100, net_pnl=0))
        with self.assertRaises(ValueError):
            self.journal.close(self.key, ID, dict(closed_at=T.isoformat(), exit_price=100))

    def test_api_authentication_and_no_order_submission(self):
        app = Flask(__name__); app.secret_key = 'fixture'
        app.register_blueprint(create_connected_blueprint(lambda: SQLiteRepository(self.path), snapshot))
        route = f'/api/portfolio/accounts/{self.key}/trades'
        with patch.dict('os.environ', {'PAPER_CONTROL_TOKEN': 'fixture'}), patch('manual_demo_journal.datetime') as clock, app.test_client() as client:
            clock.now.return_value = T
            self.assertEqual(client.get(route).status_code, 401)
            self.assertEqual(client.post(route, json=entry()).status_code, 401)
            auth = {'Authorization': 'Bearer fixture'}
            response = client.post(route, json=entry(), headers=auth)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json['order_submitted'])
            self.assertEqual(client.get(route, headers=auth).json['trades'][0]['entry']['instrument'], 'fixture-EPIC')
            self.assertEqual(client.post(route, json=[], headers=auth).status_code, 422)


if __name__ == '__main__':
    unittest.main()
