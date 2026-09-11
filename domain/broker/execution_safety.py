"""IG Demo pre-submission safety decision; contains no execution transport."""
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256

from domain.risk import RiskStatus
from .reconciliation import BrokerReconciliationResult
from .state import BrokerStateSnapshot,Freshness

VERSION="ig-demo-execution-safety-v1"
class CheckStatus(str,Enum):PASS="PASS";FAIL="FAIL";UNRESOLVED="UNRESOLVED";NOT_CONFIGURED="NOT_CONFIGURED"
def utc(x):
    if not isinstance(x,datetime) or x.tzinfo is None or x.utcoffset() is None:raise ValueError("timezone-aware evaluation required")
    return x.astimezone(timezone.utc)

@dataclass(frozen=True)
class ExecutionSafetyConfig:
    execution_enabled:bool|None=False;human_permission:bool|None=None;warning_discrepancies_block:bool|None=None;same_direction_position_blocks:bool|None=None

@dataclass(frozen=True)
class ExecutionSafetyContext:
    broker:str;environment:str;account_id:str;order_intent_id:str;intent_id:str;instrument_id:str;execution_symbol:str|None;epic:str|None;direction:str
    opportunity_id:str;policy_id:str;policy_opportunity_id:str;policy_instrument_id:str;policy_status:str;stop_price:float|None;stop_distance:float|None
    risk_evaluation_id:str|None;risk_policy_id:str|None;risk_instrument_id:str|None;risk_status:RiskStatus|None;approved_size:float|None;approved_loss_budget:float|None
    account_state:BrokerStateSnapshot|None;reconciliation:BrokerReconciliationResult|None;market_status:str|None;market_data_fresh:bool|None
    broker_submission_capability:bool;duplicate_intent:bool;kill_switch_active:bool|None;account_currency:str|None;price_currency:str|None;fx_available:bool|None;margin_required:bool;margin_metadata_available:bool
    provenance_versions:tuple[str,...];expected_provenance_versions:tuple[str,...]
    def __post_init__(self):
        if self.direction not in {"LONG","SHORT"}:raise ValueError("direction required")

@dataclass(frozen=True)
class ExecutionSafetyCheck:
    check_id:str;status:CheckStatus;mandatory:bool;reason:str
@dataclass(frozen=True)
class ExecutionSafetyDecision:
    decision_id:str;version:str;evaluated_at:datetime;broker:str;environment:str;account_id:str;order_intent_id:str;status:CheckStatus;eligible_for_submission:bool;checks:tuple[ExecutionSafetyCheck,...];blockers:tuple[str,...];warnings:tuple[str,...];provenance:str
    def __post_init__(self):object.__setattr__(self,"evaluated_at",utc(self.evaluated_at))

def evaluate_safety(context:ExecutionSafetyContext,config:ExecutionSafetyConfig,evaluated_at):
    evaluated_at=utc(evaluated_at);checks=[]
    def add(i,status,reason,mandatory=True):checks.append(ExecutionSafetyCheck(i,status,mandatory,reason))
    add("demo_environment",CheckStatus.PASS if context.broker=="IG" and context.environment=="DEMO" else CheckStatus.FAIL,"IG DEMO required")
    add("execution_feature_flag",CheckStatus.NOT_CONFIGURED if config.execution_enabled is None else CheckStatus.PASS if config.execution_enabled else CheckStatus.FAIL,"explicit Demo execution flag required")
    add("human_permission",CheckStatus.NOT_CONFIGURED if config.human_permission is None else CheckStatus.PASS if config.human_permission else CheckStatus.FAIL,"explicit human permission required")
    add("broker_capability",CheckStatus.PASS if context.broker_submission_capability else CheckStatus.FAIL,"broker submission capability remains disabled")
    snapshot=context.account_state;account=snapshot.account if snapshot else None
    add("account_enabled",CheckStatus.UNRESOLVED if account is None else CheckStatus.PASS if account.enabled is True else CheckStatus.FAIL,"enabled factual account required")
    add("account_identity_match",CheckStatus.UNRESOLVED if account is None else CheckStatus.PASS if account.account_id==context.account_id else CheckStatus.FAIL,"selected account must match snapshot")
    add("broker_state_freshness",CheckStatus.UNRESOLVED if snapshot is None else CheckStatus.PASS if snapshot.freshness is Freshness.FRESH else CheckStatus.FAIL,"fresh broker snapshot required")
    add("positions_available",CheckStatus.UNRESOLVED if snapshot is None else CheckStatus.PASS if snapshot.positions_available else CheckStatus.FAIL,"successful positions snapshot required")
    mapping_ok=bool(context.execution_symbol and context.epic and context.execution_symbol==context.epic)
    add("instrument_mapping",CheckStatus.PASS if mapping_ok else CheckStatus.FAIL,"exact execution symbol and IG EPIC required")
    add("execution_symbol",CheckStatus.PASS if context.execution_symbol else CheckStatus.UNRESOLVED,"execution symbol required")
    approved=context.risk_status in {RiskStatus.APPROVED,RiskStatus.REDUCED}
    add("risk_approval",CheckStatus.PASS if approved else CheckStatus.FAIL,"M15 APPROVED or REDUCED required")
    add("approved_size",CheckStatus.PASS if approved and context.approved_size is not None and context.approved_size>0 else CheckStatus.FAIL,"approved positive size required")
    add("approved_loss_budget",CheckStatus.PASS if approved and context.approved_loss_budget is not None and context.approved_loss_budget>0 else CheckStatus.FAIL,"approved loss budget required")
    policy_ok=context.policy_status=="READY_FOR_RISK_REVIEW"
    add("policy_resolved",CheckStatus.PASS if policy_ok else CheckStatus.FAIL,"resolved M14 policy required")
    add("stop_resolved",CheckStatus.PASS if policy_ok and context.stop_price is not None and context.stop_distance is not None else CheckStatus.UNRESOLVED,"resolved stop geometry required")
    add("market_state",CheckStatus.PASS if context.market_status=="TRADEABLE" else CheckStatus.UNRESOLVED if context.market_status is None else CheckStatus.FAIL,"current TRADEABLE market required")
    add("stale_market_data",CheckStatus.UNRESOLVED if context.market_data_fresh is None else CheckStatus.PASS if context.market_data_fresh else CheckStatus.FAIL,"fresh market data required")
    rec=context.reconciliation
    critical=rec.severity_summary.get("CRITICAL",0) if rec else None;warnings_count=rec.severity_summary.get("WARNING",0) if rec else None
    if rec is None:add("reconciliation_clean",CheckStatus.UNRESOLVED,"M27 result required")
    elif critical:add("reconciliation_clean",CheckStatus.FAIL,"critical reconciliation discrepancy")
    elif warnings_count and config.warning_discrepancies_block is None:add("reconciliation_clean",CheckStatus.NOT_CONFIGURED,"warning policy not configured")
    elif warnings_count and config.warning_discrepancies_block:add("reconciliation_clean",CheckStatus.FAIL,"warning discrepancies configured to block")
    else:add("reconciliation_clean",CheckStatus.PASS,"no blocking reconciliation discrepancy")
    add("duplicate_pending",CheckStatus.FAIL if context.duplicate_intent else CheckStatus.PASS,"stable order-intent identity must be unused")
    conflict=None
    if snapshot and snapshot.positions_available:
        relevant=[p for p in snapshot.positions if p.epic==context.epic or (p.instrument_id and p.instrument_id==context.instrument_id)]
        if any(p.mapping_status!="RESOLVED" for p in relevant):conflict="UNRESOLVED"
        elif any(p.direction!=context.direction for p in relevant):conflict="OPPOSING"
        elif relevant:conflict="SAME"
    if conflict in {"UNRESOLVED","OPPOSING"}:add("position_conflict",CheckStatus.FAIL,"unresolved/opposing position requires separate exit review")
    elif conflict=="SAME" and config.same_direction_position_blocks is None:add("position_conflict",CheckStatus.NOT_CONFIGURED,"same-direction exposure policy not configured")
    elif conflict=="SAME" and config.same_direction_position_blocks:add("position_conflict",CheckStatus.FAIL,"same-direction exposure configured to block")
    else:add("position_conflict",CheckStatus.PASS,"no blocking position conflict")
    add("kill_switch",CheckStatus.UNRESOLVED if context.kill_switch_active is None else CheckStatus.FAIL if context.kill_switch_active else CheckStatus.PASS,"kill switch must be explicitly clear")
    add("account_currency",CheckStatus.UNRESOLVED if not context.account_currency or not context.price_currency else CheckStatus.PASS if context.account_currency==context.price_currency or context.fx_available is True else CheckStatus.FAIL,"aligned currency or explicit FX required")
    add("margin_metadata",CheckStatus.PASS if not context.margin_required or context.margin_metadata_available else CheckStatus.UNRESOLVED,"required margin metadata must be factual")
    chain=(context.policy_opportunity_id==context.opportunity_id and context.risk_policy_id==context.policy_id and context.policy_instrument_id==context.instrument_id and context.risk_instrument_id==context.instrument_id and context.intent_id and context.order_intent_id)
    versions=bool(context.provenance_versions) and context.provenance_versions==context.expected_provenance_versions
    add("provenance_integrity",CheckStatus.PASS if chain and versions else CheckStatus.FAIL,"opportunity-policy-risk-intent identity/version chain must match")
    blockers=tuple(c.reason for c in checks if c.mandatory and c.status is not CheckStatus.PASS);warning_text=tuple(c.reason for c in checks if not c.mandatory and c.status is not CheckStatus.PASS)
    eligible=not blockers;status=CheckStatus.PASS if eligible else CheckStatus.FAIL if any(c.status is CheckStatus.FAIL for c in checks if c.mandatory) else CheckStatus.UNRESOLVED
    identity="|".join((context.order_intent_id,evaluated_at.isoformat(),VERSION));return ExecutionSafetyDecision("safety:"+sha256(identity.encode()).hexdigest(),VERSION,evaluated_at,context.broker,context.environment,context.account_id,context.order_intent_id,status,eligible,tuple(checks),blockers,warning_text,"authorization check only; never an order submission")

__all__=["CheckStatus","ExecutionSafetyCheck","ExecutionSafetyConfig","ExecutionSafetyContext","ExecutionSafetyDecision","VERSION","evaluate_safety"]
