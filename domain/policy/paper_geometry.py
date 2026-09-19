"""Causal close-observation geometry for PAPER research, not an OHLC fill model."""
from dataclasses import replace
from datetime import timedelta
from math import isfinite
from domain.contracts.policy import CandidateTradePolicy, EntryPolicyType, ExitPolicyType, StopPolicyType
from domain.policy.engine import TradePolicyEngine, PolicyContext
from shadow_learning import stable_id

VERSION = "paper-close-structure-v1"


def resolve_paper_policy(opportunity, *, now, observed_at, observed_price,
                         prior_closes, slippage, reward_multiple=2., max_holding_seconds=604800):
    """Freeze structure at the original decision; enter only on a later observation."""
    if now.tzinfo is None or observed_at.tzinfo is None:
        raise ValueError("aware causal clocks required")
    if not opportunity.evaluated_at < observed_at <= now:
        raise ValueError("entry requires a subsequent causal observation")
    if (now - observed_at).total_seconds() > 86400:
        raise ValueError("entry observation stale")
    if (now - opportunity.evaluated_at).total_seconds() > max_holding_seconds:
        raise ValueError("opportunity expired")
    if opportunity.eligibility_status != "ELIGIBLE" or opportunity.blockers:
        raise ValueError("eligible canonical opportunity required")
    if opportunity.direction not in {"LONG", "SHORT"} or opportunity.horizon_id != "1d":
        raise ValueError("unsupported paper direction or horizon")
    if (not isfinite(observed_price) or observed_price <= 0 or not isfinite(slippage)
            or slippage < 0 or not isfinite(reward_multiple) or reward_multiple < 1
            or max_holding_seconds <= 0):
        raise ValueError("invalid explicit geometry assumptions")
    rows = tuple(prior_closes)
    if len(rows) < 20 or any(at.tzinfo is None or at > opportunity.evaluated_at
                             or not isfinite(price) or price <= 0 for at, price in rows):
        raise ValueError("causal preceding structure unavailable")
    if any(a[0] >= b[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("structure dates must strictly increase")
    sign = 1 if opportunity.direction == "LONG" else -1
    entry = observed_price + sign * slippage
    stop = (min if sign == 1 else max)(price for _, price in rows[-20:])
    distance = sign * (entry - stop)
    if distance <= 0 or entry <= 0:
        raise ValueError("structure already invalidated at observed entry")
    target = entry + sign * distance * reward_multiple
    if target <= 0:
        raise ValueError("target outside positive price domain")
    expiry = now + timedelta(seconds=max_holding_seconds)
    context = PolicyContext(now, expiry, 86400, slippage_assumption={
        "status": "CONFIGURED_PAPER_ASSUMPTION", "per_unit": slippage})
    base = TradePolicyEngine().create(opportunity, created_at=now, context=context)
    snapshot = CandidateTradePolicy(VERSION, VERSION, EntryPolicyType.MARKET,
                                    StopPolicyType.STRUCTURAL_INVALIDATION,
                                    ExitPolicyType.RISK_REWARD_TARGET,
                                    {"structure_window": 20, "reward_multiple": reward_multiple,
                                     "session_exit": "NEXT_NEW_COMPLETE_SESSION",
                                     "model": "OBSERVED_CLOSE_ONLY"})
    return replace(base, policy_id=stable_id("paper-policy", opportunity.opportunity_id, observed_at.isoformat(), VERSION),
                   policy_version=VERSION, policy_family_id=VERSION, policy_family_version=VERSION,
                   status="READY_FOR_RISK_REVIEW", entry_type=EntryPolicyType.MARKET,
                   entry_reference="SUBSEQUENT_OBSERVED_CLOSE", entry_timing="AFTER_ORIGINAL_RANKING",
                   entry_price_source="COMPLETED_PUBLIC_CLOSE_PLUS_CONFIGURED_SLIPPAGE",
                   entry_price=entry, stop_type=StopPolicyType.STRUCTURAL_INVALIDATION,
                   stop_price=stop, stop_distance=distance, stop_reference="PRECEDING_20_CLOSE_EXTREME",
                   stop_provenance={"available_at": opportunity.evaluated_at.isoformat(), "version": VERSION},
                   target_type="RISK_REWARD_TARGET", target_reference="CONFIGURED_PAPER_R_MULTIPLE",
                   target_distance=distance * reward_multiple, target_levels=(target,),
                   target_provenance={"reward_multiple": reward_multiple, "version": VERSION},
                   reasons=("PAPER_RESEARCH_ONLY", "CLOSE_OBSERVATION_FILL_ASSUMPTION"),
                   blockers=(), family_snapshot=snapshot,
                   exit_rules=("OBSERVED_STOP", "OBSERVED_TARGET", "NEXT_NEW_COMPLETE_SESSION",
                               "TIME_EXPIRY", "OPPOSING_CANONICAL_DIRECTION"),
                   provenance={**base.provenance, "paper_only": True,
                               "entry_observed_at": observed_at.isoformat(), "geometry_version": VERSION})
