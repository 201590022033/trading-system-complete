"""Explainable research gates; execution-grade is a stricter data check only."""
from dataclasses import dataclass
from intraday_data import utc
from intraday_instruments import DataGrade
from intraday_costs import transition_cost
VERSION='intraday-gates-v1'

@dataclass(frozen=True)
class GateResult:
    checks: dict
    reasons: tuple
    research_pass: bool
    execution_grade: bool
    cost_fraction: float | None
    version: str=VERSION


def evaluate_gates(instrument,bar,session,profile,snapshot,decision,cross_asset,schedule,units=1,execution=False):
    checks={};reasons=[];now=utc(decision.decision_time)
    def check(name,state,reason):
        checks[name]=state
        if state!='PASS':reasons.append(name+':'+reason)
    check('identity','PASS' if instrument.enabled and instrument.supports_intraday and bar.instrument_id==instrument.instrument_id and snapshot.instrument_id==instrument.instrument_id else 'FAIL','DISABLED_OR_MISMATCH')
    fresh=bar.available_time<=now and bar.decision_time<=now and not bar.stale and (now-bar.event_time).total_seconds()<=bar.source.max_age_seconds
    check('freshness','PASS' if fresh else 'FAIL','STALE_OR_UNAVAILABLE')
    open_=bool(session and session.session_id==bar.session_id and session.open_time<=now<session.close_time and not any(a<=now<b for a,b in session.breaks) and bar.market_state=='OPEN')
    check('session','PASS' if open_ else 'FAIL','CLOSED_HALTED_OR_UNKNOWN')
    execution_grade=bool(bar.data_grade==DataGrade.EXECUTION and instrument.data_grade==DataGrade.EXECUTION and instrument.supports_live_data and not bar.delayed and fresh)
    check('data_grade','PASS' if not execution or execution_grade else 'FAIL','RESEARCH_OR_DELAYED_ONLY')
    volume=snapshot.values.get('relative_volume');notional=snapshot.values.get('median_quote_notional_volume')
    liquidity=(not profile.requires_volume or (volume is not None and volume>=profile.minimum_relative_volume and notional is not None and notional>=10000))
    check('liquidity','PASS' if liquidity else 'UNAVAILABLE' if volume is None or notional is None else 'FAIL','MISSING_OR_THIN_VOLUME')
    spread=bar.spread/bar.mid*10000 if bar.mid else None
    check('spread','PASS' if spread is not None and spread<=profile.maximum_spread_bps else 'FAIL' if spread is not None else 'PASS' if schedule is not None and schedule.spread_bps<=profile.maximum_spread_bps and not execution else 'UNAVAILABLE','WIDE_OR_UNKNOWN_SPREAD')
    count=sum(v is not None for v in decision.signals.values())
    check('features','PASS' if count>=3 and len(snapshot.input_record_ids)>=profile.minimum_bars else 'INSUFFICIENT_DATA','WARMUP_OR_FEW_SIGNALS')
    check('context','PASS' if cross_asset is not None and cross_asset.decision_time==now and all(f in cross_asset.values for f in profile.factors) else 'UNAVAILABLE','MISSING_ASOF_FACTORS')
    check('snapshot_clock','PASS' if snapshot.decision_time==now else 'FAIL','SNAPSHOT_DECISION_MISMATCH')
    cost=transition_cost(instrument,schedule,0,units,bar.close) if bar.close is not None else None
    fraction=2*cost.total/(abs(units)*bar.close*instrument.contract_multiplier) if cost and cost.available and units else None
    check('costs','PASS' if fraction is not None else 'UNAVAILABLE','UNKNOWN_COST_OR_SIZE')
    # ATR is observed movement, never a prediction of expected profit.
    atr=snapshot.values.get('atr')
    check('cost_viability','PASS' if fraction is not None and atr is not None and fraction<atr/bar.close else 'UNAVAILABLE' if fraction is None or atr is None else 'FAIL','COST_EXCEEDS_OBSERVED_ATR_OR_UNAVAILABLE')
    return GateResult(checks,tuple(reasons),all(s=='PASS' for s in checks.values()),execution_grade,fraction)
