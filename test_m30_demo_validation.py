import inspect,json,subprocess,sys,unittest
from dataclasses import replace
from types import SimpleNamespace
from domain.broker.execution_safety import CheckStatus
from domain.broker.ig_demo_validation import *
from domain.broker.ig_execution import DemoExecutionConfig,IGDemoOrderSubmissionAdapter,SubmissionStatus
from test_ig_demo_submission import NOW,Transport,adapter,request,safety

class State:
    def __init__(self,count=0,fail=False):self.count=count;self.fail=fail;self.calls=0
    def get_broker_snapshot(self,account):
        self.calls+=1
        if self.fail:raise RuntimeError("unavailable")
        return SimpleNamespace(position_count=self.count,positions_available=True,account=SimpleNamespace(account_id=account,environment="DEMO",enabled=True))
def plan(**changes):
    values=dict(fixture_label="M30 DEMO VALIDATION FIXTURE",request=request(),market_status="TRADEABLE",quote_fresh=True,minimum_size=1.,pre_position_count=0,pre_reconciliation_critical=0);values.update(changes);return DemoValidationPlan(**values)
def harness(transport=None,state=None):
    service=IGDemoOrderSubmissionAdapter(adapter(transport or Transport()),DemoExecutionConfig(True,True),lambda:NOW)
    reconciliation=lambda snapshot:SimpleNamespace(clean=False,severity_summary={"CRITICAL":0,"WARNING":1,"INFO":0})
    return BoundedIGDemoValidationHarness(service,state or State(),reconciliation,clock=lambda:NOW)

class M30Tests(unittest.TestCase):
    def test_default_is_non_mutating_dry_run_not_authorized(self):
        h=harness();result=h.run(plan());self.assertEqual(result.outcome,ValidationOutcome.NOT_AUTHORIZED);self.assertFalse(result.external_mutation_performed);self.assertEqual(result.mutation_count,0);self.assertTrue(result.would_send)
    def test_credentials_and_enabled_adapter_do_not_authorize(self):
        t=Transport();h=harness(t);h.run(plan());self.assertEqual(t.calls,[])
    def test_live_account_epic_market_freshness_and_reconciliation_gate(self):
        with self.assertRaises(ValueError):request(order_intent=replace(request().order_intent,mode="LIVE"))
        with self.assertRaises(RuntimeError):harness().run(plan(request=request(order_intent=replace(request().order_intent,broker_symbol="OTHER"))))
        for p in (plan(market_status="CLOSED"),plan(quote_fresh=False),plan(pre_reconciliation_critical=1)):
            self.assertEqual(harness().run(p).outcome,ValidationOutcome.BLOCKED_BY_SAFETY)
    def test_m28_pass_stop_size_and_minimum_required(self):
        self.assertEqual(harness().run(plan(request=request(safety_decision=safety(broker_submission_capability=False)))).outcome,ValidationOutcome.BLOCKED_BY_SAFETY)
        with self.assertRaises(ValueError):plan(request=request(stop_level=0))
        with self.assertRaises(RuntimeError):harness().run(plan(minimum_size=.5))
    def test_one_authorized_mutation_then_readback_and_reconciliation(self):
        t=Transport();state=State(0);h=harness(t,state);result=h.run(plan(),DemoValidationAuthorization(True));self.assertEqual(result.outcome,ValidationOutcome.CONFIRMED_POSITION_NOT_YET_VISIBLE);self.assertEqual(result.mutation_count,1);self.assertEqual(state.calls,2);self.assertFalse(result.post_reconciliation_clean);self.assertTrue(result.pre_account_read);self.assertTrue(result.post_positions_read)
        with self.assertRaises(RuntimeError):h.run(plan(),DemoValidationAuthorization(True))
        self.assertEqual(len([x for x in t.calls if x[0]=="POST"]),1)
    def test_acknowledgement_confirmation_and_reference_distinct(self):
        result=harness(Transport({"dealStatus":"PENDING"})).run(plan(),DemoValidationAuthorization(True));self.assertEqual(result.submission_status,SubmissionStatus.REQUEST_ACCEPTED.value);self.assertEqual(result.deal_reference,"REF-1");self.assertEqual(result.confirmation_status,"PENDING")
    def test_unknown_outcome_stops_and_is_not_retried(self):
        from domain.broker.ig import IGRequestError
        calls=[]
        def transport(*args):calls.append(args[0]);raise IGRequestError(None,None,"NETWORK_ERROR","network")
        h=harness(transport,State(0));result=h.run(plan(),DemoValidationAuthorization(True));self.assertEqual(result.outcome,ValidationOutcome.UNKNOWN_OUTCOME);self.assertTrue(result.unknown_outcome)
        with self.assertRaises(RuntimeError):h.run(plan(),DemoValidationAuthorization(True));self.assertEqual(calls,["POST"])
    def test_no_auto_close_and_process_warning(self):
        result=harness().run(plan());self.assertTrue(any("NO_AUTO_CLOSE" in x for x in result.warnings));self.assertTrue(any("PROCESS_LOCAL" in x for x in result.warnings));self.assertFalse(hasattr(harness(),"close"))
    def test_safe_artifact_and_masked_account(self):
        result=harness().run(plan());rendered=json.dumps(result.safe_dict());self.assertNotIn("ACC\"",rendered);self.assertIn("***CC",rendered)
        for secret in ("API_SECRET","PASSWORD","CST_SECRET","XST_SECRET"):self.assertNotIn(secret,rendered)
    def test_cli_default_never_mutates(self):
        output=subprocess.check_output([sys.executable,"-m","scripts.m30_demo_validation"],text=True);value=json.loads(output);self.assertEqual(value["external_mutation"],"NOT PERFORMED")
    def test_no_gui_autonomy_or_close_surface(self):
        source=inspect.getsource(__import__("domain.broker.ig_demo_validation",fromlist=["x"]));
        for forbidden in ("app.py","OpportunityService","close_position","DELETE","LIVE"):self.assertNotIn(forbidden,source)

if __name__=="__main__":unittest.main()
