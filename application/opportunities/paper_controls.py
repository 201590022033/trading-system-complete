"""Audited operator controls over the existing PAPER account."""
from datetime import datetime, timezone
from uuid import uuid4
from shadow_learning import stable_id

AGGRESSION = {"conservative": .5, "balanced": .75, "aggressive": 1.0}


def controls_for(state, config):
    return {"aggression": config.aggression, "paused": False, **state.get("controls", {})}


def update_controls(repository, config, changes, *, now=None):
    if not isinstance(changes, dict) or not changes or set(changes) - {"aggression", "paused"}:
        raise ValueError("choose aggression and/or paused")
    if "aggression" in changes and (not isinstance(changes["aggression"], str) or changes["aggression"] not in AGGRESSION):
        raise ValueError("aggression must be conservative, balanced or aggressive")
    if "paused" in changes and not isinstance(changes["paused"], bool):
        raise ValueError("paused must be true or false")
    at = (now or datetime.now(timezone.utc)).isoformat()
    with repository.paper_account_transaction(config.account_id) as state:
        previous = controls_for(state, config)
        current = {**previous, **changes, "updated_at": at}
        repository.save_paper_record(stable_id("paper-control", config.account_id, uuid4().hex),
            config.account_id, "control", at, {"before": previous, "after": current, "mode": "PAPER"})
        state["controls"] = current
        return current
