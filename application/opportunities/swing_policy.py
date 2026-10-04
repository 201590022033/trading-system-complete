"""Append-only cash Swing policy research beside, never inside, paper execution."""
from collections import Counter
from copy import deepcopy

from domain.policy.swing_shadow import PROFILE, VERSION, HORIZONS, rules, digest, build_policy, simulate
from domain.strategy import DEFAULT_STRATEGY_REGISTRY
from domain.strategy.attribution import fields, freeze_profile, reference, validate_frozen_profile
from shadow_learning import stable_id, timestamp
from .public_research import public_share_catalog, _identities
from .swing_technical import READ_LIMIT

DECISION_KIND = "swing-policy-decision"
ENTRY_KIND = "swing-policy-entry"
OBSERVATION_KIND = "swing-policy-observation"
OUTCOME_KIND = "swing-policy-outcome"


def frozen_definition():
    return {**freeze_profile(DEFAULT_STRATEGY_REGISTRY.resolve(PROFILE.strategy_profile_id, PROFILE.strategy_profile_version)),
            "policy_version": VERSION, "policy_rules": rules(), "policy_rules_sha256": digest(rules())}


def record_and_replay(repository, account_id, snapshots, charts, *, evaluated_at, definition):
    """Must be called in the existing account transaction; old jobs opt out."""
    if definition is None:
        return {"state": "NOT_CONFIGURED_FOR_FROZEN_JOB", "live_execution": False}
    if validate_frozen_profile(definition) != PROFILE or definition != frozen_definition():
        raise ValueError("exact frozen Swing policy definition required")
    repository.save_strategy_definition(definition)
    now = timestamp(evaluated_at)
    catalog = public_share_catalog()
    for key, features in snapshots.items():
        if key not in catalog or "session" not in features:
            continue  # ETFs and unavailable sources remain separate technical research.
        if features.get("source_symbol") != catalog[key]["yahoo_symbol"]:
            raise ValueError("policy source instrument mismatch")
        did = stable_id(DECISION_KIND, account_id, key, features["session"], VERSION, PROFILE.strategy_profile_version)
        if repository.paper_record(did) is None:
            policy = build_policy(features, decision_at=now.isoformat())
            repository.save_paper_record(did, account_id, DECISION_KIND, now.isoformat(),
                {**fields(PROFILE), "decision_id": did, "instrument_key": key,
                 "instrument_id": _identities(key, catalog[key])[0].instrument_id,
                 "policy": policy, "policy_sha256": digest(policy), "features": deepcopy(features)})
    decisions = [row for row in repository.paper_records(account_id, DECISION_KIND, as_of=now.isoformat(), limit=READ_LIMIT)
                 if reference(row) == PROFILE]
    states = Counter()
    for decision in decisions:
        policy = decision["policy"]
        if digest(policy) != decision["policy_sha256"] or digest(decision["features"]) != policy["source_feature_sha256"]:
            raise ValueError("immutable shadow decision checksum mismatch")
        if policy["state"] != "SHADOW_READY":
            states[policy["state"]] += 1
            continue
        pending = {h: stable_id(OUTCOME_KIND, decision["decision_id"], h, VERSION) for h in HORIZONS}
        pending = {h: oid for h, oid in pending.items() if repository.paper_record(oid) is None}
        if not pending:
            continue
        chart = deepcopy(charts.get(decision["instrument_key"], {}))
        # Freeze observed post-decision bars separately. Later provider revisions
        # cannot rewrite a simulated entry or an already observed stop path.
        if chart:
            from .public_research import _available_at
            rows = chart.get("bars", ())
            try:
                current_sessions = {row["timestamp"][:10] for row in rows}
                later_sessions = [row["timestamp"][:10] for row in rows
                                  if timestamp(policy["decision_at"]) < _available_at(row["timestamp"]) <= now]
            except (KeyError, TypeError, ValueError, OverflowError):
                current_sessions = set()
                later_sessions = []
            known = {}
            missing_observed = False
            for index in range(max(HORIZONS)+1):
                saved = repository.paper_record(stable_id(OBSERVATION_KIND, decision["decision_id"], index))
                if saved is not None:
                    if (reference(saved) != PROFILE or saved["decision_id"] != decision["decision_id"]
                            or digest(saved["bar"]) != saved["bar_sha256"]):
                        raise ValueError("shadow observation lineage mismatch")
                    if timestamp(saved["recorded_at"]) <= now:
                        session = saved["bar"]["timestamp"][:10]
                        missing_observed |= (session not in current_sessions or index >= len(later_sessions)
                                             or later_sessions[index] != session)
                        known[session] = saved["bar"]
            if missing_observed:
                chart = {}  # Never substitute another entry/path after truncation.
            elif known:
                chart["bars"] = [known.get(row["timestamp"][:10], row) for row in rows]
        for horizon, oid in pending.items():
            result = simulate(policy, chart, evaluated_at=now.isoformat(), horizon_sessions=horizon)
            eid = stable_id(ENTRY_KIND, decision["decision_id"])
            entry_keys = ("entry_price", "entry_session", "entry_observed_at", "stop_price", "target_price")
            saved_entry = repository.paper_record(eid)
            if saved_entry is not None and "entry_price" in result and any(saved_entry[key] != result[key] for key in entry_keys):
                result = {"state": "DATA_UNAVAILABLE"}  # Inserted history cannot replace a frozen entry.
            states[result["state"]] += 1
            for index, bar in enumerate(result.get("path", ())):
                bid = stable_id(OBSERVATION_KIND, decision["decision_id"], index)
                if repository.paper_record(bid) is None:
                    repository.save_paper_record(bid, account_id, OBSERVATION_KIND, now.isoformat(),
                        {**fields(PROFILE), "decision_id": decision["decision_id"], "recorded_at": now.isoformat(),
                         "bar": bar, "bar_sha256": digest(bar)})
            if "entry_price" in result:
                if repository.paper_record(eid) is None:
                    repository.save_paper_record(eid, account_id, ENTRY_KIND, now.isoformat(),
                        {**fields(PROFILE), "decision_id": decision["decision_id"],
                         **{key: result[key] for key in entry_keys},
                         "basis": "SHADOW_COMPLETED_CLOSE_PROXY_NOT_BROKER_FILL"})
            if result["state"] in {"CLOSED", "EXPIRED", "INVALIDATED"}:
                repository.save_paper_record(oid, account_id, OUTCOME_KIND, now.isoformat(),
                    {**result, "outcome_id": oid, "decision_id": decision["decision_id"],
                     "instrument_id": decision["instrument_id"], "recorded_at": now.isoformat()})
    outcomes = [row for row in repository.paper_records(account_id, OUTCOME_KIND, as_of=now.isoformat(), limit=READ_LIMIT)
                if reference(row) == PROFILE]
    return {**fields(PROFILE), "policy_version": VERSION, "state": "SHADOW_NOT_PROMOTED",
            "decision_count": len(decisions), "decision_states": dict(Counter(row["policy"]["state"] for row in decisions)),
            "replay_states": dict(states), "read_limit": READ_LIMIT,
            "horizons": {str(h): _summarize([row for row in outcomes if row["horizon_sessions"] == h]) for h in HORIZONS},
            "cost_basis": rules()["cost_basis"], "live_execution": False,
            "limitations": "OVERLAPPING_SIGNALS_NOT_A_PORTFOLIO; CALENDAR_LIQUIDITY_ACTUAL_COSTS_M15_UNRESOLVED; WALK_FORWARD_REQUIRED"}


def _summarize(rows):
    closed = [row for row in rows if row["state"] == "CLOSED"]
    return {"closed_count": len(closed), "terminal_states": dict(Counter(row["state"] for row in rows)),
            "ambiguous_count": sum(row["ambiguous_bar"] for row in closed),
            "negative_count_10bps": sum(row["net_return_scenarios"]["10"] < 0 for row in closed),
            "mean_net_return_scenarios": {str(bps): sum(row["net_return_scenarios"][str(bps)] for row in closed)/len(closed)
                                           if closed else None for bps in rules()["round_trip_cost_bps_scenarios"]},
            "interpretation": "DESCRIPTIVE_NOT_VALIDATED"}
