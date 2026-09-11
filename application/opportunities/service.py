"""Framework-neutral read-only orchestration over M13-M15 contracts."""
from dataclasses import dataclass
from datetime import datetime,timezone
from hashlib import sha256
from domain.evaluation.opportunity import ResearchOpportunity
from domain.policy.engine import PolicyContext,TradePolicy,TradePolicyEngine
from domain.risk import RiskEngine,RiskEvaluation,RiskStatus

VERSION='trade-intent-preview-v1'
SCORE_DESCRIPTION='comparative research score; not probability of profit'

@dataclass(frozen=True)
class TradeIntentPreview:
 intent_id:str;intent_version:str;created_at:datetime;opportunity_id:str;policy_id:str;risk_evaluation_id:str|None
 instrument_id:str;horizon_id:str;broker:str|None;broker_mapping:str|None;direction:str|None
 entry_reference:str;entry_timing:str;entry_status:str;stop_status:str;stop_reference:str
 risk_status:str;approved_loss_budget:float|None;approved_position_size:float|None
 target_status:str;time_exit:datetime|None;invalidation:str;execution_readiness:str
 blockers:tuple[str,...];provenance:dict
 def to_dict(self):
  return {'intent_id':self.intent_id,'intent_version':self.intent_version,'created_at':self.created_at.isoformat(),'opportunity_id':self.opportunity_id,'policy_id':self.policy_id,'risk_evaluation_id':self.risk_evaluation_id,'instrument_id':self.instrument_id,'horizon_id':self.horizon_id,'broker':self.broker,'broker_mapping':self.broker_mapping,'direction':self.direction,'entry':{'reference':self.entry_reference,'timing':self.entry_timing,'status':self.entry_status},'stop':{'status':self.stop_status,'reference':self.stop_reference},'risk':{'status':self.risk_status,'approved_loss_budget':self.approved_loss_budget,'approved_position_size':self.approved_position_size},'target':{'status':self.target_status,'time_exit':self.time_exit.isoformat() if self.time_exit else None},'invalidation':self.invalidation,'execution_readiness':self.execution_readiness,'blockers':list(self.blockers),'provenance':dict(self.provenance),'executable':False}

def serialize_opportunity(o):
 return {'opportunity_id':o.opportunity_id,'opportunity_version':o.opportunity_version,'evaluated_at':o.evaluated_at.isoformat(),'instrument_id':o.instrument_id,'horizon_id':o.horizon_id,'broker':o.broker,'market_mapping_status':o.market_mapping_status,'broker_mapping':o.ig_epic,'direction':o.direction,'evidence_status':o.evidence_status,'suitability_status':o.suitability_status,'research_suitability':o.research_suitability,'execution_suitability':o.execution_suitability,'data_status':o.data_status,'cost_status':o.cost_status,'liquidity_status':o.liquidity_status,'data_grade':o.data_grade,'sample_count':o.sample_count,'effective_evidence_count':o.effective_evidence_count,'ranking_score':o.ranking_score,'ranking_score_semantics':SCORE_DESCRIPTION,'rank':o.rank,'eligibility_status':o.eligibility_status,'uncertainty':list(o.uncertainty),'reasons':list(o.reasons),'blockers':list(o.blockers),'provenance':dict(o.provenance),'versions':{'ranking':o.ranking_version,'suitability':o.suitability_version,'effectiveness':o.effectiveness_version,'regime':o.regime_version,'features':list(o.input_feature_versions)}}

def serialize_policy(p):
 return {'policy_id':p.policy_id,'policy_version':p.policy_version,'created_at':p.created_at.isoformat(),'opportunity_id':p.opportunity_id,'instrument_id':p.instrument_id,'horizon_id':p.horizon_id,'direction':p.direction,'status':p.status,'actionability':p.actionability,'entry':{'type':p.entry_type.value,'reference':p.entry_reference,'timing':p.entry_timing,'price':p.entry_price,'price_source':p.entry_price_source},'stop':{'status':'UNRESOLVED' if p.stop_price is None else 'AVAILABLE','type':p.stop_type.value,'reference':p.stop_reference,'distance':p.stop_distance,'price':p.stop_price,'provenance':dict(p.stop_provenance)},'target':{'status':'NONE' if not p.target_levels else 'AVAILABLE','type':p.target_type,'levels':list(p.target_levels),'time_exit':p.time_exit_at.isoformat() if p.time_exit_at else None},'invalidation':{'reason':p.invalidation_reason,'condition':p.invalidation_condition},'risk_approval_status':p.risk_approval_status,'reasons':list(p.reasons),'blockers':list(p.blockers),'provenance':dict(p.provenance),'executable':False}

def serialize_risk(r):
 d=r.to_dict();d['status']=r.status.value;d['executable']=False;return d

class OpportunityService:
 def __init__(self,opportunities=(),policies=(),risks=()):self.replace_records(opportunities,policies,risks)
 def replace_records(self,opportunities=(),policies=(),risks=()):
  self._opportunities={x.opportunity_id:x for x in opportunities};self._policies={x.opportunity_id:x for x in policies};self._risks={x.policy_id:x for x in risks}
 def list_opportunities(self,limit=None):
  if limit is not None and (not isinstance(limit,int) or limit<1):raise ValueError('limit must be a positive integer')
  values=sorted(self._opportunities.values(),key=lambda x:(x.rank is None,x.rank or 10**9,x.opportunity_id));return tuple(values[:limit] if limit else values)
 def get_opportunity(self,oid):return self._opportunities[oid]
 def get_policy(self,oid):
  self.get_opportunity(oid);return self._policies[oid]
 def get_risk(self,oid):
  p=self.get_policy(oid);return self._risks[p.policy_id]
 def build_trade_policy(self,oid,*,created_at,context:PolicyContext):
  p=TradePolicyEngine().create(self.get_opportunity(oid),created_at=created_at,context=context);self._policies[oid]=p;return p
 def evaluate_risk(self,oid,**kwargs):
  r=RiskEngine().evaluate(self.get_policy(oid),**kwargs);self._risks[r.policy_id]=r;return r
 def get_trade_intent_preview(self,oid,created_at=None):
  o=self.get_opportunity(oid);p=self.get_policy(oid);r=self._risks.get(p.policy_id);created_at=(created_at or p.created_at).astimezone(timezone.utc)
  blockers=list(o.blockers)+list(p.blockers)+(list(r.blockers)+list(r.rejection_reasons) if r else ['RISK_EVALUATION_UNAVAILABLE'])
  if o.eligibility_status=='BLOCKED' or p.status=='BLOCKED' or (r and r.status in {RiskStatus.BLOCKED,RiskStatus.REJECTED}):ready='BLOCKED'
  elif p.stop_price is None or p.stop_distance is None or (r and r.status is RiskStatus.UNRESOLVED):ready='UNRESOLVED'
  elif r and r.status in {RiskStatus.APPROVED,RiskStatus.REDUCED} and o.execution_suitability=='EXECUTION-SUITABLE' and o.ig_epic:ready='READY_FOR_PREVIEW'
  else:ready='NOT_READY'
  identity=f'{o.opportunity_id}|{p.policy_id}|{r.evaluation_id if r else "NONE"}|{VERSION}'
  return TradeIntentPreview('intent-preview:'+sha256(identity.encode()).hexdigest(),VERSION,created_at,o.opportunity_id,p.policy_id,r.evaluation_id if r else None,o.instrument_id,o.horizon_id,o.broker,o.ig_epic,p.direction,p.entry_reference,p.entry_timing,'UNRESOLVED' if p.entry_price is None else 'AVAILABLE','UNRESOLVED' if p.stop_price is None else 'AVAILABLE',p.stop_reference,r.status.value if r else 'NOT_EVALUATED',r.approved_loss_budget if r else None,r.approved_position_size if r else None,'NONE' if not p.target_levels else 'AVAILABLE',p.time_exit_at,p.invalidation_condition,ready,tuple(dict.fromkeys(blockers)),{'opportunity_version':o.opportunity_version,'policy_version':p.policy_version,'risk_version':r.risk_version if r else None,'instrument_mapping_version':o.provenance.get('instrument_registry_version')})
