"""Explicit, gated IG Demo MARKET submission; no autonomous invocation."""
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping
from domain.contracts.trade import OrderIntent
from domain.risk import RiskEvaluation,RiskStatus
from .execution_safety import CheckStatus,ExecutionSafetyDecision,VERSION as SAFETY_VERSION
from .ig import IGRequestError,sanitize_text

VERSION="ig-demo-submission-v1"
class SubmissionStatus(str,Enum):NOT_SUBMITTED="NOT_SUBMITTED";SUBMISSION_PENDING="SUBMISSION_PENDING";REQUEST_ACCEPTED="REQUEST_ACCEPTED";BROKER_CONFIRMED="BROKER_CONFIRMED";BROKER_REJECTED="BROKER_REJECTED";UNKNOWN_OUTCOME="UNKNOWN_OUTCOME"
class DemoSubmissionError(RuntimeError):pass
@dataclass(frozen=True)
class DemoExecutionConfig:
    execution_enabled:bool=False;human_permission:bool=False
@dataclass(frozen=True)
class DemoOrderSubmissionRequest:
    order_intent:OrderIntent;safety_decision:ExecutionSafetyDecision;risk_evaluation:RiskEvaluation
    stop_level:float;expiry:str;force_open:bool;guaranteed_stop:bool;currency_code:str|None
    opportunity_version:str;intent_version:str;policy_version:str;risk_version:str
    def __post_init__(self):
        if self.order_intent.mode!="DEMO" or self.order_intent.order_type!="MARKET":raise ValueError("DEMO MARKET OrderIntent required")
        if self.stop_level<=0 or not self.expiry:raise ValueError("resolved stop and explicit expiry required")
        if self.guaranteed_stop:raise ValueError("guaranteed stops are unsupported in M29")
@dataclass(frozen=True)
class BrokerOrderConfirmation:
    deal_reference:str;deal_id:str|None;deal_status:str;reason:str|None;status:str|None;confirmed_at:datetime;raw_fields:Mapping[str,object]
    def __post_init__(self):object.__setattr__(self,"raw_fields",MappingProxyType(dict(self.raw_fields)))
@dataclass(frozen=True)
class BrokerSubmissionResult:
    submission_id:str;order_intent_id:str;safety_decision_id:str;broker:str;environment:str;account_id:str;instrument_id:str;epic:str;direction:str;quantity:float;order_type:str;status:SubmissionStatus;deal_reference:str|None;confirmation:BrokerOrderConfirmation|None;reason:str|None;submitted_at:datetime;adapter_version:str;intent_version:str;safety_version:str;risk_version:str;policy_version:str
@dataclass(frozen=True)
class SubmissionAuditEvent:
    sequence:int;submission_id:str;event_type:str;recorded_at:datetime;detail:str

class IGDemoOrderSubmissionAdapter:
    def __init__(self,adapter,config=DemoExecutionConfig(),clock=None):
        if adapter.config.environment!="DEMO":raise DemoSubmissionError("IG Demo submission rejects non-DEMO environment")
        self.adapter=adapter;self.config=config;self.clock=clock or (lambda:datetime.now(timezone.utc));self._states={};self._audit=[]
    def _event(self,sid,event,detail):self._audit.append(SubmissionAuditEvent(len(self._audit)+1,sid,event,self.clock(),sanitize_text(detail,self.adapter._secrets())))
    def audit_trail(self):return tuple(self._audit)
    def capabilities(self):return {"order_submission":"IMPLEMENTED","enabled":self.config.execution_enabled and self.config.human_permission,"environment":"DEMO","live":False}
    def _validate(self,r):
        i,s,risk=r.order_intent,r.safety_decision,r.risk_evaluation
        if not self.config.execution_enabled:raise DemoSubmissionError("Demo execution feature flag disabled")
        if not self.config.human_permission:raise DemoSubmissionError("explicit human Demo permission required")
        if s.status is not CheckStatus.PASS or not s.eligible_for_submission:raise DemoSubmissionError("matching M28 PASS required")
        if (s.environment,s.broker,s.account_id)!=("DEMO","IG",self.adapter._session.account_id):raise DemoSubmissionError("Demo account identity mismatch")
        if (s.order_intent_id,s.intent_id,s.instrument_id,s.epic)!=(i.order_intent_id,i.intent_id,i.instrument_id,i.broker_symbol):raise DemoSubmissionError("safety decision does not match OrderIntent")
        if s.risk_evaluation_id!=risk.evaluation_id or s.policy_id!=risk.policy_id or risk.instrument_id!=i.instrument_id:raise DemoSubmissionError("M15/M28 provenance mismatch")
        if risk.status not in {RiskStatus.APPROVED,RiskStatus.REDUCED} or risk.approved_position_size is None or risk.approved_loss_budget is None:raise DemoSubmissionError("valid M15 approval required")
        if i.quantity!=risk.approved_position_size:raise DemoSubmissionError("quantity must equal approved M15 size")
        if r.stop_level!=risk.stop_price or risk.stop_price is None:raise DemoSubmissionError("resolved approved stop required")
        if (r.opportunity_version,r.policy_version,r.risk_version,r.intent_version)!=s.provenance_versions:raise DemoSubmissionError("version provenance mismatch")
    def map_payload(self,r):
        self._validate(r);i=r.order_intent
        payload={"epic":i.broker_symbol,"direction":i.side,"size":i.quantity,"orderType":"MARKET","expiry":r.expiry,"forceOpen":r.force_open,"guaranteedStop":False,"stopLevel":r.stop_level}
        if r.currency_code is not None:payload["currencyCode"]=r.currency_code
        return payload
    def submit(self,request):
        i=request.order_intent;sid="submission:"+sha256((i.order_intent_id+VERSION).encode()).hexdigest()
        if i.order_intent_id in self._states:raise DemoSubmissionError("duplicate or unknown-outcome OrderIntent cannot be retried")
        payload=self.map_payload(request);now=self.clock();self._states[i.order_intent_id]=SubmissionStatus.SUBMISSION_PENDING;self._event(sid,"SUBMISSION_REQUESTED","validated explicit invocation");self._event(sid,"SAFETY_VALIDATED",request.safety_decision.decision_id);self._event(sid,"IDEMPOTENCY_PASSED",i.order_intent_id);self._event(sid,"BROKER_REQUEST_ATTEMPTED","POST /positions/otc v2")
        try:response=self.adapter._request("POST","/positions/otc",version=2,payload=payload)
        except IGRequestError as exc:
            if exc.error_category in {"NETWORK_ERROR","MALFORMED_RESPONSE","UNKNOWN_IG_ERROR"} or (exc.http_status is not None and exc.http_status>=500):
                self._states[i.order_intent_id]=SubmissionStatus.UNKNOWN_OUTCOME;self._event(sid,"UNKNOWN_OUTCOME","network outcome unknown; no retry");return self._result(request,sid,SubmissionStatus.UNKNOWN_OUTCOME,None,None,"network outcome unknown",now)
            self._states[i.order_intent_id]=SubmissionStatus.BROKER_REJECTED;self._event(sid,"BROKER_REJECTED",exc.safe_message);return self._result(request,sid,SubmissionStatus.BROKER_REJECTED,None,None,exc.safe_message,now)
        reference=response.get("dealReference")
        if not reference:
            self._states[i.order_intent_id]=SubmissionStatus.UNKNOWN_OUTCOME;self._event(sid,"UNKNOWN_OUTCOME","acceptance omitted deal reference");return self._result(request,sid,SubmissionStatus.UNKNOWN_OUTCOME,None,None,"acceptance omitted deal reference",now)
        self._states[i.order_intent_id]=SubmissionStatus.REQUEST_ACCEPTED;self._event(sid,"BROKER_RESPONSE","request accepted; confirmation required")
        try:confirm=self.adapter._request("GET","/confirms/"+str(reference),version=1)
        except IGRequestError as exc:
            self._event(sid,"CONFIRMATION_UNAVAILABLE",exc.safe_message);return self._result(request,sid,SubmissionStatus.REQUEST_ACCEPTED,str(reference),None,"confirmation unavailable",now)
        confirmation=BrokerOrderConfirmation(str(reference),confirm.get("dealId"),str(confirm.get("dealStatus") or "UNKNOWN"),confirm.get("reason"),confirm.get("status"),self.clock(),{k:confirm.get(k) for k in ("dealId","dealStatus","reason","status")})
        status=SubmissionStatus.BROKER_CONFIRMED if confirmation.deal_status=="ACCEPTED" else SubmissionStatus.BROKER_REJECTED if confirmation.deal_status=="REJECTED" else SubmissionStatus.REQUEST_ACCEPTED
        self._states[i.order_intent_id]=status;self._event(sid,"CONFIRMATION_LOOKUP",status.value);return self._result(request,sid,status,str(reference),confirmation,confirmation.reason,now)
    def _result(self,r,sid,status,reference,confirmation,reason,at):
        i=r.order_intent;return BrokerSubmissionResult(sid,i.order_intent_id,r.safety_decision.decision_id,"IG","DEMO",r.safety_decision.account_id,i.instrument_id,i.broker_symbol,i.side,i.quantity,i.order_type,status,reference,confirmation,reason,at,VERSION,r.intent_version,SAFETY_VERSION,r.risk_version,r.policy_version)

__all__=["BrokerOrderConfirmation","BrokerSubmissionResult","DemoExecutionConfig","DemoOrderSubmissionRequest","DemoSubmissionError","IGDemoOrderSubmissionAdapter","SubmissionAuditEvent","SubmissionStatus","VERSION"]
