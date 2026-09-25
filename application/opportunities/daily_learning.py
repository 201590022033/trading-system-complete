"""Compact causal learning for ranked long swing candidates.

One immutable decision is stored per instrument and completed daily bar.  The
decision is labelled only after the configured number of later completed bars
exists.  Full chart histories are deliberately not copied into these records.
"""

from math import isfinite

from domain.evaluation.effectiveness import FeatureOutcome
from shadow_learning import stable_id, timestamp


VERSION = "ranked-long-swing-v1"
FEATURE_ID = "ranked_long_3_session"
DECISION_KIND = "learning-decision"
OUTCOME_KIND = "learning-outcome"
DEFAULT_HORIZON_SESSIONS = 3
DEFAULT_COST_BPS = 10.0
MAX_RECORDS = 1000


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
