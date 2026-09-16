"""Explicit synthetic session/price evidence for isolated ledger contract tests."""
from datetime import timedelta
from shadow_learning import ShadowDecision, timestamp
from shadow_learning_pipeline import label_decision

def decision(*args, **kwargs):
    result = ShadowDecision(*args, **kwargs)
    start = timestamp(result.decided_at)
    sessions = []
    for offset in range(2):
        close = start + timedelta(days=offset)
        sessions.append(dict(session_id=str(offset), session_date=close.date().isoformat(),
            open_time=(close-timedelta(hours=8)).isoformat(), close_time=close.isoformat(),
            calendar_version="synthetic-test-sessions-v1"))
    from dataclasses import replace
    return replace(result, horizon_context={"sessions": sessions})

def complete_label(decision, **kwargs):
    return label_decision(decision, entry_at=decision.decided_at, exit_at=kwargs["now"],
        entry_available_at=decision.decided_at, exit_available_at=kwargs["now"], **kwargs)
