"""Manually invoked, two-phase bounded IG Demo validation harness."""
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import Enum
from types import MappingProxyType
from typing import Callable,Mapping
from .execution_safety import CheckStatus
from .ig_execution import DemoOrderSubmissionRequest,IGDemoOrderSubmissionAdapter,SubmissionStatus

VERSION="m30-demo-validation-v1"
class ValidationOutcome(str,Enum):DRY_RUN_ONLY="DRY_RUN_ONLY";NOT_AUTHORIZED="NOT_AUTHORIZED";BLOCKED_BY_SAFETY="BLOCKED_BY_SAFETY";BROKER_REJECTED="BROKER_REJECTED";UNKNOWN_OUTCOME="UNKNOWN_OUTCOME";CONFIRMED="CONFIRMED";CONFIRMED_POSITION_VISIBLE="CONFIRMED_POSITION_VISIBLE";CONFIRMED_POSITION_NOT_YET_VISIBLE="CONFIRMED_POSITION_NOT_YET_VISIBLE"
@dataclass(frozen=True)
class DemoValidationAuthorization:
    external_demo_order_authorized:bool=False;closing_order_authorized:bool=False
@dataclass(frozen=True)
class DemoValidationPlan:
    fixture_label:str;request:DemoOrderSubmissionRequest;market_status:str;quote_fresh:bool;minimum_size:float;pre_position_count:int;pre_reconciliation_critical:int;single_process:bool=True
    def __post_init__(self):
        if self.fixture_label!="M30 DEMO VALIDATION FIXTURE":raise ValueError("isolated M30 fixture label required")
        if self.minimum_size<=0:raise ValueError("factual positive broker minimum required")
@dataclass(frozen=True)
class DemoValidationReport:
    version:str;run_at:datetime;outcome:ValidationOutcome;external_authorized:bool;external_mutation_performed:bool;environment:str;masked_account_id:str;instrument_id:str;epic:str;direction:str;size:float;stop_level:float;market_status:str;safety_status:str;would_send:Mapping[str,object];mutation_count:int;request_transmitted:bool;http_acknowledged:bool;submission_status:str|None;deal_reference:str|None;deal_id:str|None;confirmation_status:str|None;broker_reason:str|None;pre_account_read:bool;pre_positions_read:bool;pre_position_count:int;post_account_read:bool;post_positions_read:bool;post_position_count:int|None;post_reconciliation_clean:bool|None;post_reconciliation_summary:Mapping[str,int]|None;unknown_outcome:bool;warnings:tuple[str,...]
    def __post_init__(self):
        object.__setattr__(self,"would_send",MappingProxyType(dict(self.would_send)))
        if self.post_reconciliation_summary is not None:object.__setattr__(self,"post_reconciliation_summary",MappingProxyType(dict(self.post_reconciliation_summary)))
    def safe_dict(self):
        value=dict(self.__dict__);value["run_at"]=self.run_at.isoformat();value["outcome"]=self.outcome.value;value["would_send"]=dict(self.would_send);value["post_reconciliation_summary"]=dict(self.post_reconciliation_summary) if self.post_reconciliation_summary is not None else None;value["warnings"]=list(self.warnings);return value

def _mask(value):return "***"+value[-2:] if value else "UNAVAILABLE"
class BoundedIGDemoValidationHarness:
    def __init__(self,submission:IGDemoOrderSubmissionAdapter,state_service,pre_reconcile:Callable,post_reconcile:Callable|None=None,clock=None):
        self.submission=submission;self.state_service=state_service;self.pre_reconcile=pre_reconcile;self.post_reconcile=post_reconcile or pre_reconcile;self.clock=clock or (lambda:datetime.now(timezone.utc));self._mutation_count=0
    def run(self,plan:DemoValidationPlan,authorization=DemoValidationAuthorization()):
        r=plan.request;i=r.order_intent;s=r.safety_decision
        if i.mode!="DEMO" or s.environment!="DEMO":raise RuntimeError("M30 is DEMO only")
        if s.account_id!=self.submission.adapter._session.account_id:raise RuntimeError("exact Demo account required")
        if i.broker_symbol!=s.epic:raise RuntimeError("exact EPIC required")
        if plan.market_status!="TRADEABLE" or not plan.quote_fresh:outcome=ValidationOutcome.BLOCKED_BY_SAFETY
        elif plan.pre_reconciliation_critical:outcome=ValidationOutcome.BLOCKED_BY_SAFETY
        elif s.status is not CheckStatus.PASS or not s.eligible_for_submission:outcome=ValidationOutcome.BLOCKED_BY_SAFETY
        elif i.quantity!=plan.minimum_size:raise RuntimeError("validation size must equal factual broker minimum")
        elif not plan.single_process:raise RuntimeError("single controlled process required")
        else:outcome=ValidationOutcome.NOT_AUTHORIZED if not authorization.external_demo_order_authorized else None
        payload=self.submission.map_payload(r) if outcome is not ValidationOutcome.BLOCKED_BY_SAFETY else {}
        if outcome is not None:return self._report(plan,authorization,outcome,payload,None,None,None,None,False)
        if self._mutation_count:raise RuntimeError("M30 permits one opening mutation maximum")
        # Re-read factual broker state and M27 immediately before the sole mutation.
        pre_snapshot=self.state_service.get_broker_snapshot(s.account_id)
        pre_result=self.pre_reconcile(pre_snapshot)
        critical=int(pre_result.severity_summary.get("CRITICAL",0))
        account=pre_snapshot.account
        if account.account_id!=s.account_id or account.environment!="DEMO" or account.enabled is not True:raise RuntimeError("exact enabled Demo account required")
        if not pre_snapshot.positions_available or pre_snapshot.position_count!=plan.pre_position_count:raise RuntimeError("position preflight changed")
        if critical:raise RuntimeError("M27 critical discrepancy blocks submission")
        self._mutation_count=1;result=self.submission.submit(r)
        # Every post-send operation below is read-only. No close method exists here.
        try:snapshot=self.state_service.get_broker_snapshot(s.account_id);post_count=snapshot.position_count;rec=self.post_reconcile(snapshot);clean=rec.clean;summary=rec.severity_summary
        except Exception:post_count=None;clean=None;summary=None
        if result.status is SubmissionStatus.UNKNOWN_OUTCOME:outcome=ValidationOutcome.UNKNOWN_OUTCOME
        elif result.status is SubmissionStatus.BROKER_REJECTED:outcome=ValidationOutcome.BROKER_REJECTED
        elif result.status is SubmissionStatus.BROKER_CONFIRMED:outcome=ValidationOutcome.CONFIRMED_POSITION_VISIBLE if post_count is not None and post_count>plan.pre_position_count else ValidationOutcome.CONFIRMED_POSITION_NOT_YET_VISIBLE
        else:outcome=ValidationOutcome.CONFIRMED
        return self._report(plan,authorization,outcome,payload,result,post_count,clean,summary,True)
    def _report(self,p,a,outcome,payload,result,post_count,clean,summary,pre_read):
        r=p.request;i=r.order_intent;s=r.safety_decision;confirmation=result.confirmation if result else None
        warnings=("PROCESS_LOCAL_IDEMPOTENCY; DO NOT RUN CONCURRENTLY OR RESTART DURING SUBMISSION","NO_AUTO_CLOSE; OPEN AUTHORIZATION DOES NOT AUTHORIZE CLOSE")
        acknowledged=bool(result and result.deal_reference)
        return DemoValidationReport(VERSION,self.clock(),outcome,a.external_demo_order_authorized,result is not None,"DEMO",_mask(s.account_id),i.instrument_id,i.broker_symbol,i.side,i.quantity,r.stop_level,p.market_status,s.status.value,payload,self._mutation_count,result is not None,acknowledged,result.status.value if result else None,result.deal_reference if result else None,confirmation.deal_id if confirmation else None,confirmation.deal_status if confirmation else None,result.reason if result else None,pre_read,pre_read,p.pre_position_count,post_count is not None,post_count is not None,post_count,clean,summary,outcome is ValidationOutcome.UNKNOWN_OUTCOME,warnings)

__all__=["BoundedIGDemoValidationHarness","DemoValidationAuthorization","DemoValidationPlan","DemoValidationReport","ValidationOutcome","VERSION"]
