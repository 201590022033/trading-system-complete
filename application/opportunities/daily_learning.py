"""Compact causal evidence for daily cash-share swing research.

One immutable decision is stored per instrument and completed daily bar.  The
decision is labelled only after the configured number of later completed bars
exists.  Full chart histories are deliberately not copied into these records.
"""

from math import isfinite
from statistics import mean

from domain.evaluation.effectiveness import FeatureOutcome
from shadow_learning import stable_id, timestamp


VERSION = "ranked-long-swing-v1"
FEATURE_ID = "ranked_long_3_session"
DECISION_KIND = "learning-decision"
OUTCOME_KIND = "learning-outcome"
DEFAULT_HORIZON_SESSIONS = 3
DEFAULT_COST_BPS = 10.0
MAX_RECORDS = 5000
PANEL_VERSION = "daily-candidate-panel-v1"
PANEL_DECISION_KIND = "candidate-decision"
PANEL_OUTCOME_KIND = "candidate-outcome"


def _time(value):
    return timestamp(value.isoformat() if hasattr(value, "isoformat") else value)


def _outcome_id(decision_id):
    return stable_id("ranked-long-swing-outcome", decision_id)


def record_decisions(repository, account_id, opportunities, series, *, evaluated_at,
                     horizon_sessions=DEFAULT_HORIZON_SESSIONS,
                     cost_bps=DEFAULT_COST_BPS):
    """Persist at most one compact LONG decision per instrument/session."""
    now = _time(evaluated_at)
    saved = 0
    instrument_to_symbol = {
        values["instrument_id"]: symbol for symbol, values in series.items()
    }
    for opportunity in opportunities:
        if opportunity.rank is None or opportunity.rank > 5 or opportunity.direction != "LONG":
            continue
        symbol = instrument_to_symbol.get(opportunity.instrument_id)
        if symbol is None:
            continue
        bars = series[symbol]["bars"]
        if not bars:
            continue
        entry_at, entry_close, _ = bars[-1]
        decision_id = stable_id(
            "ranked-long-swing-decision", account_id, opportunity.instrument_id,
            entry_at.isoformat(), VERSION,
        )
        if repository.paper_record(decision_id) is not None:
            continue
        payload = {
            "decision_id": decision_id,
            "version": VERSION,
            "feature_id": FEATURE_ID,
            "mode": "SHADOW_RESEARCH",
            "instrument_id": opportunity.instrument_id,
            "symbol": symbol,
            "direction": "LONG",
            "rank": opportunity.rank,
            "opportunity_id": opportunity.opportunity_id,
            "decision_at": now.isoformat(),
            "entry_bar_at": entry_at.isoformat(),
            "entry_close": entry_close,
            "horizon_sessions": horizon_sessions,
            "cost_bps": cost_bps,
            "regime_version": opportunity.regime_version,
            "regime_state": opportunity.regime_context.get("trend"),
            "ranking_version": opportunity.ranking_version,
        }
        repository.save_paper_record(
            decision_id, account_id, DECISION_KIND, now.isoformat(), payload
        )
        saved += 1
    return saved


def label_matured(repository, account_id, series, *, evaluated_at):
    """Label decisions only from later completed bars already available now."""
    now = _time(evaluated_at)
    labelled = 0
    decisions = repository.paper_records(
        account_id, DECISION_KIND, as_of=now.isoformat(), limit=MAX_RECORDS
    )
    for decision in decisions:
        outcome_id = _outcome_id(decision["decision_id"])
        if repository.paper_record(outcome_id) is not None:
            continue
        values = series.get(decision["symbol"])
        if values is None:
            continue
        later = [bar for bar in values["bars"]
                 if bar[0] > _time(decision["entry_bar_at"])]
        horizon = int(decision["horizon_sessions"])
        if len(later) < horizon:
            continue
        exit_at, exit_close, _ = later[horizon - 1]
        if exit_at > now:
            continue
        entry_close = float(decision["entry_close"])
        gross = float(exit_close) / entry_close - 1.0
        net = gross - float(decision["cost_bps"]) / 10000.0
        if not all(isfinite(value) for value in (entry_close, exit_close, gross, net)):
            continue
        payload = {
            "outcome_id": outcome_id,
            "decision_id": decision["decision_id"],
            "version": VERSION,
            "feature_id": FEATURE_ID,
            "mode": "SHADOW_RESEARCH",
            "instrument_id": decision["instrument_id"],
            "direction": "LONG",
            "decision_at": decision["decision_at"],
            "entry_bar_at": decision["entry_bar_at"],
            "exit_bar_at": exit_at.isoformat(),
            "entry_close": entry_close,
            "exit_close": float(exit_close),
            "horizon_sessions": horizon,
            "gross_return": gross,
            "net_return": net,
            "cost_bps": float(decision["cost_bps"]),
            "label": "WIN" if net > 0 else "LOSS" if net < 0 else "FLAT",
            "recorded_at": now.isoformat(),
            "regime_version": decision.get("regime_version"),
            "regime_state": decision.get("regime_state"),
            "opportunity_id": decision["opportunity_id"],
        }
        repository.save_paper_record(
            outcome_id, account_id, OUTCOME_KIND, exit_at.isoformat(), payload
        )
        labelled += 1
    return labelled


def feature_outcomes(repository, account_id, *, evaluated_at):
    """Adapt matured compact outcomes to the existing causal learner."""
    now = _time(evaluated_at)
    rows = repository.paper_records(
        account_id, OUTCOME_KIND, as_of=now.isoformat(), limit=MAX_RECORDS
    )
    result = []
    for row in rows:
        if row.get("version") != VERSION or row.get("feature_id") != FEATURE_ID:
            continue
        result.append(FeatureOutcome(
            FEATURE_ID, VERSION, "strategy", row["instrument_id"], "1d",
            row.get("regime_version"), row.get("regime_state"), 1,
            _time(row["decision_at"]), _time(row["entry_bar_at"]),
            _time(row["exit_bar_at"]), float(row["gross_return"]),
            float(row["net_return"]), row["outcome_id"],
        ))
    return tuple(result)


def record_candidate_panel(repository, account_id, opportunities, series, *, evaluated_at,
                           horizon_sessions=DEFAULT_HORIZON_SESSIONS,
                           cost_bps=DEFAULT_COST_BPS, market_context=None,
                           sectors=None, decision_kind=PANEL_DECISION_KIND):
    """Freeze one compact point-in-time row for every screened share/session."""
    now = _time(evaluated_at)
    instrument_to_symbol = {row["instrument_id"]: symbol for symbol, row in series.items()}
    saved = 0
    for opportunity in opportunities:
        symbol = instrument_to_symbol.get(opportunity.instrument_id)
        if symbol is None or not series[symbol]["bars"]:
            continue
        signal_at, signal_close, _ = series[symbol]["bars"][-1]
        record_id = stable_id("daily-candidate", account_id, opportunity.instrument_id,
                              signal_at.isoformat(), PANEL_VERSION)
        if repository.paper_record(record_id) is not None:
            continue
        evidence = opportunity.input_evidence
        technical = evidence.get("technical") or {}
        news = evidence.get("news_macro") or {}
        swing = evidence.get("swing_history") or {}
        items = news.get("items") or ()
        news_scores = []
        for item in items:
            try:
                score = float(item["score"])
            except (KeyError, TypeError, ValueError):
                continue
            if isfinite(score):
                news_scores.append(score)
        selected = (opportunity.rank is not None and opportunity.rank <= 5
                    and opportunity.direction == "LONG"
                    and opportunity.eligibility_status == "ELIGIBLE")
        payload = {
            "decision_id": record_id, "version": PANEL_VERSION,
            "mode": "SHADOW_RESEARCH", "instrument_id": opportunity.instrument_id,
            "symbol": symbol, "decision_at": now.isoformat(),
            "signal_bar_at": signal_at.isoformat(), "signal_close": signal_close,
            "direction": opportunity.direction, "eligibility_status": opportunity.eligibility_status,
            "rank": opportunity.rank, "ranking_score": opportunity.ranking_score,
            "market_state": (market_context or {}).get("state", "INSUFFICIENT_CONTEXT"),
            "sector": (sectors or {}).get(symbol, "UNCLASSIFIED"),
            "selected": selected, "opportunity_id": opportunity.opportunity_id,
            "ranking_version": opportunity.ranking_version,
            "momentum_20d_signal": technical.get("momentum_20d_signal"),
            "rsi_14_signal": technical.get("rsi_14_signal"),
            "swing_setup": swing.get("setup", "UNAVAILABLE"),
            "swing_market_state": swing.get("market_state", "UNKNOWN"),
            "swing_history_version": swing.get("version"),
            "swing_history_source_sha256": swing.get("source_sha256"),
            "regime_state": opportunity.regime_context.get("trend"),
            "volatility_state": opportunity.regime_context.get("volatility"),
            "news_state": news.get("state", "UNAVAILABLE"),
            "news_score": mean(news_scores) if news_scores else None,
            "horizon_sessions": horizon_sessions, "cost_bps": cost_bps,
        }
        repository.save_paper_record(record_id, account_id, decision_kind,
                                     now.isoformat(), payload)
        saved += 1
    return saved


def label_candidate_panel(repository, account_id, series, *, evaluated_at,
                          decision_kind=PANEL_DECISION_KIND, outcome_kind=PANEL_OUTCOME_KIND):
    """Use the next completed close as entry proxy, then hold three sessions."""
    now = _time(evaluated_at)
    saved = 0
    decisions = repository.paper_records(
        account_id, decision_kind, as_of=now.isoformat(), limit=MAX_RECORDS)
    for decision in decisions:
        outcome_id = stable_id("daily-candidate-outcome", decision["decision_id"])
        if repository.paper_record(outcome_id) is not None:
            continue
        values = series.get(decision["symbol"])
        if values is None:
            continue
        later = [bar for bar in values["bars"]
                 if bar[0] > max(_time(decision["signal_bar_at"]), _time(decision["decision_at"]))]
        horizon = int(decision["horizon_sessions"])
        if len(later) <= horizon:
            continue
        entry_at, entry_close, _ = later[0]
        exit_at, exit_close, _ = later[horizon]
        if exit_at > now or not all(isfinite(float(price)) and float(price) > 0
                                    for price in (entry_close, exit_close)):
            continue
        gross = float(exit_close) / float(entry_close) - 1
        net = gross - float(decision["cost_bps"]) / 10000
        payload = {
            "outcome_id": outcome_id, "decision_id": decision["decision_id"],
            "version": PANEL_VERSION, "mode": "SHADOW_RESEARCH",
            "instrument_id": decision["instrument_id"], "symbol": decision["symbol"],
            "signal_bar_at": decision["signal_bar_at"],
            "entry_bar_at": entry_at.isoformat(), "exit_bar_at": exit_at.isoformat(),
            "entry_close": float(entry_close), "exit_close": float(exit_close),
            "gross_return": gross, "net_return": net,
            "cost_bps": float(decision["cost_bps"]),
            "horizon_sessions": horizon,
            "label": "WIN" if net > 0 else "LOSS" if net < 0 else "FLAT",
            "selected": decision["selected"], "recorded_at": now.isoformat(),
            "market_state": decision.get("market_state", "INSUFFICIENT_CONTEXT"),
            "swing_setup": decision.get("swing_setup", "UNAVAILABLE"),
            "swing_market_state": decision.get("swing_market_state", "UNKNOWN"),
            "swing_history_version": decision.get("swing_history_version"),
            "swing_history_source_sha256": decision.get("swing_history_source_sha256"),
            "sector": decision.get("sector", "UNCLASSIFIED"),
        }
        repository.save_paper_record(outcome_id, account_id, outcome_kind,
                                     exit_at.isoformat(), payload)
        saved += 1
    return saved


def candidate_panel_summary(repository, account_id, *, evaluated_at, outcome_kind=PANEL_OUTCOME_KIND):
    """Report matched selected-versus-other outcomes; never infer trade skill."""
    now = _time(evaluated_at)
    rows = repository.paper_records(
        account_id, outcome_kind, as_of=now.isoformat(), limit=MAX_RECORDS)
    groups = {}
    states = {}
    for row in rows:
        if row.get("version") != PANEL_VERSION:
            continue
        key = (row["signal_bar_at"], row["entry_bar_at"], row["exit_bar_at"])
        groups.setdefault(key, {"selected": [], "other": []})[
            "selected" if row["selected"] else "other"].append(float(row["net_return"]))
        states[key] = row.get("market_state", "INSUFFICIENT_CONTEXT")
    pairs = []
    for key, group in sorted(groups.items()):
        if group["selected"] and group["other"]:
            pairs.append((key, mean(group["selected"]), mean(group["other"])))
    nonoverlap = []
    last_exit = None
    for pair in pairs:
        if last_exit is None or _time(pair[0][1]) > last_exit:
            nonoverlap.append(pair)
            last_exit = _time(pair[0][2])
    by_market_state = {}
    for pair in nonoverlap:
        by_market_state.setdefault(states[pair[0]], []).append((pair[1], pair[2]))
    return {
        "state": "COLLECTING_COMPARISONS" if len(nonoverlap) < 30 else "READY_FOR_REVIEW",
        "version": PANEL_VERSION, "horizon_sessions": DEFAULT_HORIZON_SESSIONS,
        "outcome_count": sum(len(group["selected"]) + len(group["other"])
                             for group in groups.values()),
        "selected_outcome_count": sum(len(group["selected"]) for group in groups.values()),
        "comparison_outcome_count": sum(len(group["other"]) for group in groups.values()),
        "paired_sessions": len(pairs), "nonoverlapping_paired_sessions": len(nonoverlap),
        "minimum_nonoverlapping_sessions": 30,
        "mean_selected_net_return": mean(pair[1] for pair in nonoverlap) if nonoverlap else None,
        "mean_other_net_return": mean(pair[2] for pair in nonoverlap) if nonoverlap else None,
        "mean_selection_edge": mean(pair[1] - pair[2] for pair in nonoverlap)
                               if nonoverlap else None,
        "by_market_state": {state: {"nonoverlapping_sessions": len(pairs_in_state),
                                     "mean_selected_net_return": mean(p[0] for p in pairs_in_state),
                                     "mean_other_net_return": mean(p[1] for p in pairs_in_state),
                                     "mean_selection_edge": mean(p[0] - p[1] for p in pairs_in_state),
                                     "selected_loss_session_fraction": sum(p[0] < 0 for p in pairs_in_state) / len(pairs_in_state),
                                     "state": "COLLECTING" if len(pairs_in_state) < 30 else "READY_FOR_REVIEW"}
                            for state, pairs_in_state in sorted(by_market_state.items())},
        "basis": "NEXT_COMPLETED_CLOSE_PROXY; MATCHED_SESSION; DECLARED_10_BPS_COST",
        "governance": "DESCRIPTIVE_RESEARCH_ONLY",
    }
