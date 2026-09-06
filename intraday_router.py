"""Pure paper-preview boundary: no provider dispatch or live order method exists."""
from dataclasses import dataclass
from datetime import timedelta
import math
from intraday_data import utc
from intraday_costs import transition_cost
from provider_interfaces import LiveExecutionDisabled
VERSION='intraday-paper-router-v1'

@dataclass(frozen=True)
class PaperPreview:
    instrument_id: str
    underlying_id: str
    signal_target_id: str
    units: float
    price: float
    currency: str
    estimated_entry_cost: float
    schedule_id: str
    assumptions: tuple
    mode: str='PAPER_ONLY'
    version: str=VERSION

@dataclass(frozen=True)
class RouterResult:
    accepted: bool
    preview: PaperPreview | None
    reasons: tuple
    version: str=VERSION


def preview(registry,instrument_id,decision,bar,session,gates,schedule,admission,now,units=1):
    reasons=[];now=utc(now)
    try:instrument=registry.get(instrument_id)
    except KeyError:return RouterResult(False,None,('UNKNOWN_INSTRUMENT',))
    if not instrument.enabled or not instrument.supports_intraday:reasons.append('DISABLED_OR_UNSUPPORTED_INSTRUMENT')
    if not decision.shadow_only:reasons.append('NON_SHADOW_DECISION')
    if not decision.cell or decision.cell[0]!=instrument_id or bar.instrument_id!=instrument_id:reasons.append('IDENTITY_MISMATCH')
    if admission!='ADMIT_FOR_CONTINUED_SHADOW':reasons.append('RESEARCH_ADMISSION_FAILED')
    if not gates.research_pass or any(state!='PASS' for state in gates.checks.values()):reasons.append('RESEARCH_GATES_FAILED')
    if now<decision.decision_time or bar.available_time>decision.decision_time or now-bar.event_time>timedelta(seconds=bar.source.max_age_seconds) or bar.stale:reasons.append('STALE_OR_FUTURE_DATA')
    if not session or session.session_id!=bar.session_id or not session.open_time<=now<session.close_time or any(a<=now<b for a,b in session.breaks) or bar.market_state!='OPEN':reasons.append('SESSION_NOT_OPEN')
    if decision.score is None or not math.isfinite(decision.score) or decision.score==0:reasons.append('NO_DIRECTIONAL_SIGNAL')
    side=1 if decision.score is not None and decision.score>0 else -1
    if units<=0:reasons.append('INVALID_SIZE')
    cost=transition_cost(instrument,schedule,0,side*units,bar.close) if bar.close is not None else None
    if cost is None or not cost.available:reasons.extend(cost.reasons if cost else ('MISSING_PRICE',))
    if reasons:return RouterResult(False,None,tuple(dict.fromkeys(reasons)))
    return RouterResult(True,PaperPreview(instrument_id,instrument.underlying_id,instrument.signal_target_id,side*units,
        bar.close,instrument.currency,cost.total,schedule.schedule_id,schedule.assumptions),())


def submit_order(*args,**kwargs):
    raise LiveExecutionDisabled('HR11 only returns hypothetical paper previews; order submission is disabled')


def cancel_order(*args,**kwargs):
    raise LiveExecutionDisabled('HR11 has no broker connection or live orders')
