"""Bridge existing frozen technical/policy output without changing installed profiles."""
from decimal import Decimal
from domain.policy.swing_shadow import PROFILE, VERSION, rules
from domain.strategy.attribution import reference, fields
from domain.backtest.engine import Signal
from shadow_learning import timestamp


def from_frozen_policy(policy, manifest, *, max_notional, risk_budget, horizon=3):
    if reference(policy)!=PROFILE or policy.get('policy_version')!=VERSION or policy.get('rules')!=rules():
        raise ValueError('exact frozen Swing 1.2.0 policy required')
    if policy.get('state')!='SHADOW_READY' or policy['source_symbol']!=manifest.instrument:
        raise ValueError('matching ready policy required')
    bars=[b for b in manifest.bars if b.session==policy['signal_session']]
    if len(bars)!=1 or Decimal(str(bars[0].close))!=Decimal(str(policy['signal_close'])):
        raise ValueError('signal provenance mismatch')
    return Signal(policy['source_feature_sha256'],manifest.instrument,policy['signal_session'],
                  timestamp(policy['decision_at']),Decimal(str(policy['stop_price'])),
                  Decimal(str(max_notional)),Decimal(str(risk_budget)),horizon=horizon,**fields(policy))
