"""Deterministic lifecycle helpers; callers supply causal market data."""
from datetime import datetime, timezone
from shadow_learning import OutcomeLabel
from indicator_effectiveness import signal_outcome
from shadow_learning import AdaptiveEvidence, timestamp
from intraday_sessions import SessionWindow, validate_sessions
from intraday_horizons import get_horizon
from indicator_effectiveness import HORIZONS

def production_shadow_decision(service, symbol: str, *, horizon: str = "5",
                                observation_id: str = "", decided_at: str = "",
                                observation=None, horizon_context=None, previous_signal=0.0):
    """Record the canonical OperationalIntelligence assessment as shadow state."""
    from shadow_learning import ShadowDecision
    from instrument_registry import resolve_instrument
    symbol = resolve_instrument(symbol).instrument_id
    context = None
    if observation is not None:
        if observation.instrument != symbol or timestamp(observation.observed_at) != timestamp(decided_at) or str(observation.horizon) != str(horizon):
            raise ValueError("observation/decision context mismatch")
        observation_id = observation.observation_id
        context = {"history": observation.market_data.get("history", [])}
    if not observation_id:
        raise ValueError("observation identity required")
    run = service.analyze(symbol, horizon=horizon, provider="historical", allow_network=False,
                          as_of=decided_at, observation_context=context)
    decision = run["decision"]
    return ShadowDecision(
        decision_id=f"decision:{observation_id or symbol}:{decided_at}",
        observation_id=observation_id, instrument=symbol, decided_at=decided_at,
        horizon=horizon, action=str(decision["action"]).upper(),
        production_assessment=decision, horizon_context=horizon_context or {},
        previous_signal=previous_signal,
        provenance={"as_of": timestamp(decided_at).isoformat(), "components": run["components"],
                    "gates": run["gates"]})

def maturity_target(decision):
    """Resolve against supplied versioned sessions; never infer holidays or bars."""
    decided = timestamp(decision.decided_at)
    sessions = validate_sessions(SessionWindow(**{**s,
        "open_time": timestamp(s["open_time"]), "close_time": timestamp(s["close_time"]),
        "breaks": tuple((timestamp(a), timestamp(b)) for a, b in s.get("breaks", []))})
        for s in decision.horizon_context.get("sessions", []))
    horizon = str(decision.horizon)
    if horizon.isdigit() and int(horizon) in HORIZONS:
        # Daily horizons are forward trading sessions from a daily close.
        indexes = [i for i, session in enumerate(sessions) if session.close_time == decided]
        if not indexes or indexes[0] + int(horizon) >= len(sessions):
            return None
        return sessions[indexes[0] + int(horizon)].close_time
    try:
        canonical = get_horizon(horizon)
    except KeyError:
        return None
    for session in sessions:
        target = canonical.target(decided, session)
        if target is not None and target > decided:
            return target
    return None

def matured(decision, now: str) -> bool:
    target = maturity_target(decision)
    return target is not None and target > timestamp(decision.decided_at) and timestamp(now) >= target

def label_decision(decision, *, now: str, entry_price: float | None, exit_price: float | None,
                   cost_model: str = "existing", entry_at="", exit_at="",
                   entry_available_at="", exit_available_at="") -> OutcomeLabel:
    if not matured(decision, now):
        raise ValueError("outcome horizon has not matured")
    if cost_model != "existing":
        raise ValueError("unsupported shadow cost model")
    target = maturity_target(decision).isoformat()
    metadata = dict(evaluated_at=now, entry_at=entry_at, exit_at=exit_at,
                    entry_available_at=entry_available_at, exit_available_at=exit_available_at)
    complete = all((entry_at, exit_at, entry_available_at, exit_available_at))
    if complete:
        complete = (timestamp(entry_at) == timestamp(decision.decided_at)
                    and timestamp(exit_at) == timestamp(target)
                    and timestamp(entry_at) <= timestamp(entry_available_at) <= timestamp(decision.decided_at)
                    and timestamp(exit_at) <= timestamp(exit_available_at) <= timestamp(now))
    if entry_price is None or exit_price is None or not complete:
        return OutcomeLabel(f"outcome:{decision.decision_id}", decision.decision_id, target,
                            "OUTCOME_DATA_UNAVAILABLE", entry_price, exit_price,
                            data_quality="INCOMPLETE", cost_model=cost_model, **metadata)
    from shadow_learning import _finite
    for price in (entry_price, exit_price):
        _finite(price)
        if price <= 0: raise ValueError("price must be positive")
    raw_return = (exit_price - entry_price) / entry_price
    signal = {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0}[decision.action]
    gross, _, net = signal_outcome(signal, decision.previous_signal, raw_return)
    return OutcomeLabel(f"outcome:{decision.decision_id}", decision.decision_id, target,
                        "HOLD" if not signal else "WIN" if gross > 0 else "LOSS",
                        entry_price, exit_price, gross, net, cost_model, **metadata)

def aggregate_evidence(repository, outcome: OutcomeLabel, *, instrument: str,
                        horizon: str, regime: str = "UNKNOWN", profile: str = "production") -> bool:
    """Contribute one valid label to one shadow evidence cell, once."""
    if outcome.label not in {"WIN", "LOSS"} or outcome.net_return is None:
        return False
    from shadow_learning_validation import validate_contribution
    validate_contribution(repository, outcome, instrument, horizon)
    now = outcome.matured_at
    evidence = AdaptiveEvidence(
        evidence_id=f"evidence:{instrument}:{horizon}:{regime}:{profile}",
        instrument=instrument, horizon=horizon, regime=regime, profile=profile,
        sample_count=1, wins=1 if outcome.label == "WIN" else 0,
        losses=1 if outcome.label == "LOSS" else 0,
        mean_net_return=outcome.net_return, reliability_state="OBSERVED",
        updated_at=now)
    return repository.contribute_adaptive_evidence(evidence, outcome.outcome_id)
