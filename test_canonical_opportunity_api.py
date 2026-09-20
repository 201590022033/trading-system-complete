import unittest
from unittest.mock import patch
from dataclasses import replace
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from domain.risk import RiskEvaluation, RiskStatus, ApprovedRiskIntent
from application.opportunities.service import OpportunityService, serialize_opportunity
from app import app, canonical_opportunity_service
from provider_interfaces import PaperExecutionProvider, LiveExecutionDisabled
import test_trade_policy


class CanonicalOpportunityApiTests(unittest.TestCase):
    def setUp(self):
        helper = test_trade_policy.TradePolicyTests()
        helper.setUp()
        self.helper = helper
        self.o1 = helper.opportunity()
        self.o2 = replace(helper.opportunity(direction='WATCH', status='WATCH'), opportunity_id='opp-2', ranking_score=50., rank=2)
        self.blocked = replace(helper.opportunity(status='BLOCKED'), opportunity_id='opp-3')
        self.p1 = helper.policy(self.o1)
        self.p2 = helper.policy(self.o2)
        self.p3 = helper.policy(self.blocked)
        self.r1 = RiskEvaluation('risk-1', 'risk-exposure-v1', helper.now, self.p1.policy_id, self.o1.instrument_id,
                                 RiskStatus.UNRESOLVED, None, None, None, None, None, self.p1.entry_reference,
                                 None, None, None, None, None, None, (), (), ('STOP_GEOMETRY_UNRESOLVED',), {}, {})
        canonical_opportunity_service.replace_records((self.o2, self.blocked, self.o1), (self.p1, self.p2, self.p3), (self.r1,))
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        canonical_opportunity_service.replace_records()

    def test_list_top_n_serialization_score_semantics_and_stable_ids(self):
        data = self.client.get('/api/v1/opportunities?limit=1').get_json()
        self.assertEqual(data['count'], 1)
        item = data['opportunities'][0]
        self.assertEqual(item['opportunity_id'], 'opp-1')
        self.assertIn('not probability', item['ranking_score_semantics'])
        self.assertNotIn('probability', item)
        self.assertEqual(item['opportunity_id'], self.client.get('/api/v1/opportunities?limit=1').get_json()['opportunities'][0]['opportunity_id'])

    def test_detail_blocked_watch_and_provenance(self):
        self.assertEqual(self.client.get('/api/v1/opportunities/opp-2').get_json()['opportunity']['eligibility_status'], 'WATCH')
        b = self.client.get('/api/v1/opportunities/opp-3').get_json()['opportunity']
        self.assertEqual(b['eligibility_status'], 'BLOCKED')
        self.assertIn('versions', b)
        self.assertIn('+00:00', b['evaluated_at'])

    def test_policy_preserves_unresolved_stop(self):
        p = self.client.get('/api/v1/opportunities/opp-1/policy').get_json()['policy']
        self.assertEqual(p['stop']['status'], 'UNRESOLVED')
        self.assertIsNone(p['stop']['price'])
        self.assertFalse(p['executable'])

    def test_risk_and_null_size_preserved(self):
        r = self.client.get('/api/v1/opportunities/opp-1/risk').get_json()['risk']
        self.assertEqual(r['status'], 'UNRESOLVED')
        self.assertIsNone(r['approved_position_size'])

    def test_intent_unresolved_readiness_and_409(self):
        response = self.client.get('/api/v1/opportunities/opp-1/intent')
        self.assertEqual(response.status_code, 409)
        body = response.get_json()
        self.assertEqual(body['intent']['execution_readiness'], 'UNRESOLVED')
        self.assertEqual(body['intent']['stop']['status'], 'UNRESOLVED')
        self.assertFalse(body['intent']['executable'])

    def test_intent_public_cash_share_ready_for_preview_without_ig_epic(self):
        """Public cash-share opportunities have no IG EPIC but should still preview when risk approves."""
        now = datetime(2026, 9, 11, 10, tzinfo=timezone.utc)
        opportunity = replace(self.o1, broker=None, market_mapping_status="UNAVAILABLE",
                              ig_epic=None, execution_suitability="EXECUTION-SUITABLE")
        policy = SimpleNamespace(
            policy_id="policy-public", policy_version="trade-policy-v1", created_at=now,
            opportunity_id=opportunity.opportunity_id, instrument_id=opportunity.instrument_id,
            horizon_id=opportunity.horizon_id, direction="LONG", status="READY_FOR_RISK_REVIEW",
            entry_reference="NEXT_OBSERVED_CANONICAL_BAR_OPEN", entry_timing="AFTER_POLICY_CREATION",
            entry_price=100.0, stop_reference="FIXED_DISTANCE", stop_price=95.0, stop_distance=5.0,
            target_levels=(), time_exit_at=now + timedelta(minutes=30),
            invalidation_condition="OPPORTUNITY_BECOMES_INELIGIBLE",
            blockers=(), reasons=())
        approved_intent = ApprovedRiskIntent(
            policy.policy_id, opportunity.instrument_id, 10.0, 1000.0, 1.0, 0.0, 50.0, "ZAR")
        risk = SimpleNamespace(
            evaluation_id="risk-public", risk_version="risk-exposure-v1", evaluated_at=now,
            policy_id=policy.policy_id, instrument_id=opportunity.instrument_id,
            status=RiskStatus.APPROVED, blockers=(), rejection_reasons=(),
            approved_loss_budget=50.0, approved_position_size=10.0,
            approved_intent=approved_intent)
        service = OpportunityService((opportunity,), (policy,), (risk,))
        preview = service.get_trade_intent_preview(opportunity.opportunity_id)
        self.assertEqual(preview.execution_readiness, "READY_FOR_PREVIEW")
        self.assertIsNone(preview.broker_mapping)
        self.assertIn("CASH_SHARE_BROKER_MAPPING_UNAVAILABLE_RESEARCH_ONLY", preview.blockers)
        # Via API the intent remains non-executable and the route returns 200 because it is ready for preview.
        with app.test_client() as client:
            canonical_opportunity_service.replace_records((opportunity,), (policy,), (risk,))
            response = client.get(f'/api/v1/opportunities/{opportunity.opportunity_id}/intent')
            body = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(body['intent']['execution_readiness'], "READY_FOR_PREVIEW")
            self.assertFalse(body['intent']['executable'])
            self.assertFalse(body['intent'].get('live_execution', False))

    def test_structured_errors(self):
        self.assertEqual(self.client.get('/api/v1/opportunities/missing').get_json()['error']['http_status'], 404)
        self.assertEqual(self.client.get('/api/v1/opportunities?limit=0').status_code, 422)
        canonical_opportunity_service.replace_records((self.o1,), (), ())
        self.assertEqual(self.client.get('/api/v1/opportunities/opp-1/risk').status_code, 503)

    def test_serialization_excludes_secrets(self):
        text = str(serialize_opportunity(self.o1)).lower()
        self.assertNotIn('api_key', text)
        self.assertNotIn('password', text)
        self.assertNotIn('security-token', text)

    def test_legacy_endpoint_and_no_execution_remain(self):
        self.assertIn('/api/opportunities', {rule.rule for rule in app.url_map.iter_rules()})
        self.assertFalse(hasattr(canonical_opportunity_service, 'submit_order'))
        with self.assertRaises(LiveExecutionDisabled):
            PaperExecutionProvider().submit_order({})

    def test_compatibility_endpoint_cannot_call_legacy_scanner(self):
        canonical_opportunity_service.replace_records((self.o1,), (), ())
        with patch('app.feeds.opportunities', side_effect=AssertionError('legacy scanner used')):
            response = self.client.get('/api/opportunities')
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body['canonical'])
        self.assertEqual(body['data']['method'], 'canonical M13 research ranking')
        self.assertEqual(body['data']['opportunities'][0]['opportunity_id'], 'opp-1')


if __name__ == '__main__':
    unittest.main()
