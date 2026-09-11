import inspect,json,unittest
from datetime import datetime,timezone
from types import MappingProxyType

from domain.broker.execution_safety import evaluate_safety
from domain.broker.ig import IGConfig,IGReadOnlyAdapter,IGRequestError,IGSession
from domain.broker.ig_execution import *
from domain.contracts.trade import OrderIntent
from domain.risk import ApprovedRiskIntent,RiskEvaluation,RiskStatus
from test_execution_safety import context as safety_context,config as safety_config

NOW=datetime(2026,9,11,12,tzinfo=timezone.utc)
def intent(**changes):
    values=dict(order_intent_id="OI",intent_id="TI",instrument_id="BRENT",broker_symbol="EPIC",side="BUY",order_type="MARKET",price=0.,quantity=1.,time_in_force="IOC",client_order_id="CID",mode="DEMO",dispatched_at=NOW);values.update(changes);return OrderIntent(**values)
def risk(**changes):
    approved=ApprovedRiskIntent("POL","BRENT",1,75,1,5,5,"USD")
    values=dict(evaluation_id="RISK",risk_version="risk-v1",evaluated_at=NOW,policy_id="POL",instrument_id="BRENT",status=RiskStatus.APPROVED,requested_loss_budget=5,requested_risk_fraction=.01,requested_gearing=1,stop_distance=5,stop_price=70,entry_reference="NEXT_OPEN",approved_loss_budget=5,approved_position_size=1,approved_notional=75,approved_gearing=1,estimated_margin=5,estimated_loss_at_stop=5,reduction_reasons=(),rejection_reasons=(),blockers=(),hard_limit_checks={"all": "PASS"},provenance={"policy_id":"POL"},approved_intent=approved);values.update(changes);return RiskEvaluation(**values)
def safety(**changes):return evaluate_safety(safety_context(**changes),safety_config(),NOW)
def request(**changes):
    values=dict(order_intent=intent(),safety_decision=safety(),risk_evaluation=risk(),stop_level=70,expiry="-",force_open=True,guaranteed_stop=False,currency_code="USD",opportunity_version="opp-v1",intent_version="intent-v1",policy_version="policy-v1",risk_version="risk-v1");values.update(changes);return DemoOrderSubmissionRequest(**values)
class Transport:
    def __init__(self,confirmation=None):self.calls=[];self.confirmation=confirmation or {"dealStatus":"ACCEPTED","dealId":"D1","status":"OPENED"}
    def __call__(self,method,url,headers,body,timeout):
        self.calls.append((method,url,json.loads(body) if body else None))
        payload={"dealReference":"REF-1"} if method=="POST" else self.confirmation
        return 200,{},json.dumps(payload).encode()
def adapter(transport=None,environment="DEMO"):
    a=IGReadOnlyAdapter(IGConfig("API_SECRET","user","PASSWORD",environment=environment),transport or Transport());a._session=IGSession("CST_SECRET","XST_SECRET","ACC");return a

class SubmissionTests(unittest.TestCase):
    def test_deterministic_mapping_and_confirmation(self):
        t=Transport();service=IGDemoOrderSubmissionAdapter(adapter(t),DemoExecutionConfig(True,True),lambda:NOW);result=service.submit(request())
        self.assertEqual(result.status,SubmissionStatus.BROKER_CONFIRMED);self.assertEqual(result.deal_reference,"REF-1");self.assertEqual(result.confirmation.deal_id,"D1")
        self.assertEqual(t.calls[0][0],"POST");self.assertTrue(t.calls[0][1].endswith("/positions/otc"));self.assertEqual(t.calls[0][2],{"epic":"EPIC","direction":"BUY","size":1.0,"orderType":"MARKET","expiry":"-","forceOpen":True,"guaranteedStop":False,"stopLevel":70,"currencyCode":"USD"})
        self.assertEqual(t.calls[1][0],"GET");self.assertIn("/confirms/REF-1",t.calls[1][1])
    def test_live_rejected_before_request_construction(self):
        t=Transport()
        with self.assertRaises(DemoSubmissionError):IGDemoOrderSubmissionAdapter(adapter(t,"LIVE"),DemoExecutionConfig(True,True))
        self.assertEqual(t.calls,[])
    def test_safety_pass_exact_intent_and_account_required(self):
        for value in (request(safety_decision=safety(broker_submission_capability=False)),request(order_intent=intent(order_intent_id="OTHER")),request(safety_decision=safety(account_id="OTHER"))):
            with self.assertRaises(DemoSubmissionError):IGDemoOrderSubmissionAdapter(adapter(),DemoExecutionConfig(True,True)).submit(value)
    def test_flags_default_disabled_and_human_permission_required(self):
        self.assertFalse(DemoExecutionConfig().execution_enabled)
        for c in (DemoExecutionConfig(),DemoExecutionConfig(True,False)):
            with self.assertRaises(DemoSubmissionError):IGDemoOrderSubmissionAdapter(adapter(),c).submit(request())
        caps=adapter().capabilities();self.assertEqual(caps["demo_order_submission"],"IMPLEMENTED_DISABLED");self.assertFalse(caps["order_submission"])
    def test_m15_size_stop_and_current_unresolved_chain_block(self):
        invalid_risk=risk(status=RiskStatus.UNRESOLVED,approved_loss_budget=None,approved_position_size=None,approved_notional=None,approved_gearing=None,estimated_margin=None,estimated_loss_at_stop=None,approved_intent=None)
        for value in (request(risk_evaluation=invalid_risk),request(order_intent=intent(quantity=.5)),request(stop_level=69),request(safety_decision=safety(policy_status="UNRESOLVED",stop_price=None,stop_distance=None))):
            with self.assertRaises((DemoSubmissionError,ValueError)):IGDemoOrderSubmissionAdapter(adapter(),DemoExecutionConfig(True,True)).submit(value)
    def test_exact_epic_and_market_only(self):
        with self.assertRaises(DemoSubmissionError):IGDemoOrderSubmissionAdapter(adapter(),DemoExecutionConfig(True,True)).submit(request(order_intent=intent(broker_symbol="OTHER")))
        with self.assertRaises(ValueError):request(order_intent=intent(order_type="LIMIT"))
    def test_explicit_native_metadata_and_no_arbitrary_defaults(self):
        with self.assertRaises(ValueError):request(expiry="")
        with self.assertRaises(ValueError):request(guaranteed_stop=True)
        payload=IGDemoOrderSubmissionAdapter(adapter(),DemoExecutionConfig(True,True)).map_payload(request(currency_code=None));self.assertNotIn("currencyCode",payload);self.assertNotIn("level",payload);self.assertNotIn("limitLevel",payload)
    def test_stable_identity_duplicate_and_unknown_not_retried(self):
        t=Transport();service=IGDemoOrderSubmissionAdapter(adapter(t),DemoExecutionConfig(True,True),lambda:NOW);first=service.submit(request())
        with self.assertRaisesRegex(DemoSubmissionError,"duplicate"):service.submit(request())
        self.assertEqual(len([x for x in t.calls if x[0]=="POST"]),1);self.assertTrue(first.submission_id.startswith("submission:"))
    def test_network_after_send_is_unknown_and_never_retried(self):
        calls=[]
        def transport(*args):calls.append(args[0]);raise IGRequestError(None,None,"NETWORK_ERROR","IG could not be reached")
        service=IGDemoOrderSubmissionAdapter(adapter(transport),DemoExecutionConfig(True,True),lambda:NOW);result=service.submit(request());self.assertEqual(result.status,SubmissionStatus.UNKNOWN_OUTCOME)
        with self.assertRaises(DemoSubmissionError):service.submit(request())
        self.assertEqual(calls,["POST"])
    def test_rejection_and_http_acceptance_are_distinct_from_confirmation(self):
        def rejected(*args):raise IGRequestError(400,"error.reject","MALFORMED_REQUEST","broker rejected")
        result=IGDemoOrderSubmissionAdapter(adapter(rejected),DemoExecutionConfig(True,True),lambda:NOW).submit(request());self.assertEqual(result.status,SubmissionStatus.BROKER_REJECTED);self.assertIn("rejected",result.reason)
        t=Transport({"dealStatus":"PENDING"});result=IGDemoOrderSubmissionAdapter(adapter(t),DemoExecutionConfig(True,True),lambda:NOW).submit(request());self.assertEqual(result.status,SubmissionStatus.REQUEST_ACCEPTED);self.assertIsNone(result.confirmation.deal_id)
    def test_audit_append_only_and_secrets_absent(self):
        service=IGDemoOrderSubmissionAdapter(adapter(),DemoExecutionConfig(True,True),lambda:NOW);service.submit(request());events=service.audit_trail();self.assertGreaterEqual(len(events),6);self.assertEqual([x.sequence for x in events],list(range(1,len(events)+1)))
        rendered=repr(events)
        for secret in ("API_SECRET","PASSWORD","CST_SECRET","XST_SECRET"):self.assertNotIn(secret,rendered)
    def test_no_gui_or_autonomous_or_live_execution_path(self):
        source=inspect.getsource(__import__("domain.broker.ig_execution",fromlist=["x"]));self.assertNotIn("app.py",source);self.assertNotIn("OpportunityService",source);self.assertNotIn("LIVE",source.replace("non-DEMO", ""))

if __name__=="__main__":unittest.main()
