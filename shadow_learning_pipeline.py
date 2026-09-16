"""Deterministic lifecycle helpers; callers supply causal market data."""
from datetime import datetime, timezone, timedelta
from shadow_learning import OutcomeLabel
from indicator_effectiveness import signal_outcome
from shadow_learning import AdaptiveEvidence

def production_shadow_decision(service, symbol: str, *, horizon: str = "swing",
                                observation_id: str = "", decided_at: str = ""):
    """Record the canonical OperationalIntelligence assessment as shadow state."""
    from shadow_learning import ShadowDecision
    run = service.analyze(symbol, horizon=horizon, provider="historical", allow_network=False)
    decision = run["decision"]
    return ShadowDecision(
        decision_id=f"decision:{observation_id or symbol}:{decided_at}",
        observation_id=observation_id, instrument=symbol, decided_at=decided_at,
        horizon=horizon, action=str(decision["action"]).upper(),
        production_assessment=decision)

def matured(decision, now: str) -> bool:
    current = datetime.fromisoformat(now.replace('Z','+00:00'))
    decided = datetime.fromisoformat(decision.decided_at.replace('Z','+00:00'))
    horizon = decision.horizon
    if isinstance(horizon, int) or (isinstance(horizon, str) and horizon.isdigit()):
        target = decided + timedelta(days=int(horizon))
    elif isinstance(horizon, str) and horizon.startswith("intraday_") and horizon.endswith("m"):
        target = decided + timedelta(minutes=int(horizon[9:-1]))
    else:
        # EOD/session horizons require the caller to provide the canonical
        # matured timestamp; equality at decision time is never sufficient.
        return current > decided and horizon in {"intraday_eod", "eod"}
    return current >= target

def label_decision(decision, *, now: str, entry_price: float | None, exit_price: float | None,
                   cost_model: str = "existing") -> OutcomeLabel:
    if not matured(decision, now):
        raise ValueError("outcome horizon has not matured")
    if entry_price is None or exit_price is None:
        return OutcomeLabel(f"outcome:{decision.decision_id}", decision.decision_id, now,
                            "OUTCOME_DATA_UNAVAILABLE", entry_price or 0.0,
                            data_quality="INCOMPLETE", cost_model=cost_model)
    gross = (exit_price - entry_price) / entry_price if decision.action == "BUY" else ((entry_price - exit_price) / entry_price if decision.action == "SELL" else 0.0)
    _, _, net = signal_outcome(1.0 if decision.action == "BUY" else -1.0 if decision.action == "SELL" else 0.0, 0.0, gross)
    return OutcomeLabel(f"outcome:{decision.decision_id}", decision.decision_id, now,
                        "WIN" if gross > 0 else "LOSS", entry_price, exit_price, gross,
                        net, cost_model)

def aggregate_evidence(repository, outcome: OutcomeLabel, *, instrument: str,
                        horizon: str, regime: str = "UNKNOWN", profile: str = "production") -> bool:
    """Contribute one valid label to one shadow evidence cell, once."""
    if outcome.label not in {"WIN", "LOSS"} or outcome.net_return is None:
        return False
    now = outcome.matured_at
    evidence = AdaptiveEvidence(
        evidence_id=f"evidence:{instrument}:{horizon}:{regime}:{profile}",
        instrument=instrument, horizon=horizon, regime=regime, profile=profile,
        sample_count=1, wins=1 if outcome.label == "WIN" else 0,
        losses=1 if outcome.label == "LOSS" else 0,
        mean_net_return=outcome.net_return, reliability_state="OBSERVED",
        updated_at=now)
    return repository.contribute_adaptive_evidence(evidence, outcome.outcome_id)
