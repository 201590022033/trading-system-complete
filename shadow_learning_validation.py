"""Shared fail-closed relationship checks for both ledger backends."""
from datetime import datetime, timezone

from shadow_learning import ObservationRecord, ShadowDecision, OutcomeLabel, timestamp


def validate_decision(repository, decision):
    decision = ShadowDecision(**decision.to_dict())
    data = repository.get_observation(decision.observation_id)
    if data is None:
        raise ValueError("persisted observation required")
    observation = ObservationRecord(**data)
    if (decision.instrument, str(decision.horizon), decision.decided_at) != (
            observation.instrument, str(observation.horizon), observation.observed_at):
        raise ValueError("decision must match its causal observation")
    if decision.outcome_status != "PENDING_OUTCOME":
        raise ValueError("new decisions must be pending")


def validate_outcome(repository, outcome, *, now=None):
    from shadow_learning_pipeline import maturity_target, label_decision
    outcome = OutcomeLabel(**outcome.to_dict())
    data = repository.get_shadow_decision(outcome.decision_id)
    if data is None:
        raise ValueError("persisted decision required")
    decision = ShadowDecision(**data)
    observation = repository.get_observation(decision.observation_id)
    if observation is None or observation["instrument"] != decision.instrument:
        raise ValueError("persisted matching observation required")
    target = maturity_target(decision)
    now = timestamp(now) if now else datetime.now(timezone.utc)
    if (target is None or target != timestamp(outcome.matured_at) or not outcome.evaluated_at
            or not target <= timestamp(outcome.evaluated_at) <= now):
        raise ValueError("unresolved, premature or future outcome")
    expected = label_decision(decision, now=outcome.evaluated_at,
        entry_price=outcome.entry_price, exit_price=outcome.exit_price,
        cost_model=outcome.cost_model, entry_at=outcome.entry_at, exit_at=outcome.exit_at,
        entry_available_at=outcome.entry_available_at, exit_available_at=outcome.exit_available_at)
    for field in ("label", "data_quality", "gross_return", "net_return"):
        if getattr(outcome, field) != getattr(expected, field):
            raise ValueError("outcome does not match canonical evaluation")
    return decision


def validate_contribution(repository, outcome, instrument, horizon):
    stored = repository.get_outcome(outcome.outcome_id)
    if stored is None or OutcomeLabel(**stored) != outcome:
        raise ValueError("identical persisted outcome required")
    decision = validate_outcome(repository, outcome)
    if (decision.instrument, str(decision.horizon)) != (instrument, str(horizon)):
        raise ValueError("cross-instrument or horizon contribution")
    if outcome.label not in {"WIN", "LOSS"} or outcome.data_quality != "COMPLETE":
        raise ValueError("valid active outcome required")


def validate_evidence(repository, evidence, outcome_id):
    stored = repository.get_outcome(outcome_id)
    if stored is None:
        raise ValueError("persisted outcome required")
    outcome = OutcomeLabel(**stored)
    validate_contribution(repository, outcome, evidence.instrument, evidence.horizon)
    if not evidence.updated_at or not timestamp(outcome.evaluated_at)<=timestamp(evidence.updated_at)<=datetime.now(timezone.utc):
        raise ValueError('contribution timestamp must follow a valid evaluated outcome')
    if (evidence.sample_count != 1 or evidence.wins != int(outcome.label == "WIN")
            or evidence.losses != int(outcome.label == "LOSS")
            or evidence.mean_net_return != outcome.net_return
            or evidence.governance_state != "SHADOW_ADAPTIVE_EVIDENCE"):
        raise ValueError("contribution must represent exactly one canonical outcome")
