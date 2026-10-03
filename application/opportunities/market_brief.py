"""Small, causal cross-market context and human-review brief for the daily worker."""
from datetime import timedelta
from math import isfinite
from statistics import mean

from market_chart_registry import MARKET_CHART_INSTRUMENTS
from shadow_learning import stable_id, timestamp
from domain.strategy.attribution import fields, reference, identity_suffix, same_strategy
from .public_research import _available_at, public_share_catalog


CONTEXT_ETFS = ("ETF_STX40", "ETF_STXFIN", "ETF_STXRES", "ETF_STXIND")
VERSION = "daily-market-brief-v1"
BENCHMARK_VERSION = "daily-etf-context-v1"
BENCHMARK_DECISION_KIND = "benchmark-decision"
BENCHMARK_OUTCOME_KIND = "benchmark-outcome"
MAX_BENCHMARK_RECORDS = 5000


def _time(value):
    return timestamp(value.isoformat() if hasattr(value, "isoformat") else value)


def _etf_series(chart, evaluated_at):
    if not chart or chart.get("interval") != "1d" or chart.get("currency") != "ZAR":
        return ()
    usable = []
    for bar in chart.get("bars", ()):
        try:
            at = _available_at(bar["timestamp"])
            close = float(bar["close"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if at <= evaluated_at and isfinite(close) and close > 0:
            usable.append((at, close))
    if any(left[0] >= right[0] for left, right in zip(usable, usable[1:])):
        return ()
    return tuple(usable)


def _etf_momentum(chart, evaluated_at):
    usable = _etf_series(chart, evaluated_at)
    if len(usable) < 21:
        return None
    if evaluated_at - usable[-1][0] > timedelta(days=4):
        return None
    return {"session_at": usable[-1][0].isoformat(),
            "return_20_sessions": usable[-1][1] / usable[-21][1] - 1}


def record_benchmark_decisions(repository, account_id, context_charts, market_context, *, evaluated_at,
                               strategy_profile=None):
    """Freeze four ETF trend hypotheses, not ETF trade recommendations."""
    now = _time(evaluated_at)
    saved = 0
    for key, movement in market_context["benchmarks"].items():
        if key not in CONTEXT_ETFS:
            continue
        record_id = stable_id("daily-benchmark", account_id, key, movement["session_at"],
                              BENCHMARK_VERSION + identity_suffix(strategy_profile))
        if repository.paper_record(record_id) is not None:
            continue
        values = _etf_series(context_charts[key], now)
        if not values or values[-1][0].isoformat() != movement["session_at"]:
            continue
        payload = {**fields(strategy_profile), "decision_id": record_id, "version": BENCHMARK_VERSION,
                   "mode": "SHADOW_RESEARCH", "benchmark_id": key,
                   "signal_bar_at": movement["session_at"],
                   "market_state": market_context["state"],
                   "momentum_20_sessions": movement["return_20_sessions"],
                   "horizon_sessions": 3, "decision_at": now.isoformat()}
        repository.save_paper_record(record_id, account_id, BENCHMARK_DECISION_KIND,
                                     now.isoformat(), payload)
        saved += 1
    return saved


def label_benchmark_decisions(repository, account_id, context_charts, *, evaluated_at):
    now = _time(evaluated_at)
    saved = 0
    decisions = repository.paper_records(account_id, BENCHMARK_DECISION_KIND,
                                         as_of=now.isoformat(), limit=MAX_BENCHMARK_RECORDS)
    for decision in decisions:
        outcome_id = stable_id("daily-benchmark-outcome", decision["decision_id"])
        if repository.paper_record(outcome_id) is not None:
            continue
        key = decision["benchmark_id"]
        chart = context_charts.get(key)
        if chart is None or chart.get("symbol") != MARKET_CHART_INSTRUMENTS[key].data_symbol:
            continue
        later = [(at, close) for at, close in _etf_series(chart, now)
                 if at > max(_time(decision["signal_bar_at"]), _time(decision["decision_at"]))]
        if len(later) <= decision["horizon_sessions"]:
            continue
        entry_at, entry_close = later[0]
        exit_at, exit_close = later[decision["horizon_sessions"]]
        payload = {**fields(decision), "outcome_id": outcome_id, "decision_id": decision["decision_id"],
                   "version": BENCHMARK_VERSION, "mode": "SHADOW_RESEARCH",
                   "benchmark_id": key, "market_state": decision["market_state"],
                   "signal_bar_at": decision["signal_bar_at"],
                   "entry_bar_at": entry_at.isoformat(), "exit_bar_at": exit_at.isoformat(),
                   "gross_return": exit_close / entry_close - 1,
                   "basis": "LISTED_ETF_CLOSE_PROXY_BEFORE_COSTS", "recorded_at": now.isoformat()}
        repository.save_paper_record(outcome_id, account_id, BENCHMARK_OUTCOME_KIND,
                                     exit_at.isoformat(), payload)
        saved += 1
    return saved


def benchmark_learning_summary(repository, account_id, *, evaluated_at, strategy_profile=None):
    """Independent-session descriptive evidence against cash, never a forecast."""
    now = _time(evaluated_at)
    rows = repository.paper_records(account_id, BENCHMARK_OUTCOME_KIND,
                                    as_of=now.isoformat(), limit=MAX_BENCHMARK_RECORDS)
    groups = {}
    for row in rows:
        if row.get("version") == BENCHMARK_VERSION and reference(row) == reference(strategy_profile):
            groups.setdefault((row["benchmark_id"], row["market_state"]), []).append(row)
    result = {}
    for (key, state), items in sorted(groups.items()):
        nonoverlap, last_exit = [], None
        for item in sorted(items, key=lambda x: x["entry_bar_at"]):
            if last_exit is None or _time(item["entry_bar_at"]) > last_exit:
                nonoverlap.append(item["gross_return"])
                last_exit = _time(item["exit_bar_at"])
        result.setdefault(key, {})[state] = {
            "nonoverlapping_sessions": len(nonoverlap),
            "mean_gross_return": mean(nonoverlap),
            "loss_session_fraction": sum(value < 0 for value in nonoverlap) / len(nonoverlap),
            "state": "COLLECTING" if len(nonoverlap) < 30 else "READY_FOR_REVIEW"}
    return {**fields(strategy_profile), "version": BENCHMARK_VERSION, "basis": "LISTED_ETF_CLOSE_PROXY_BEFORE_COSTS",
            "comparison": "CASH_ZERO_GROSS_RETURN", "by_benchmark_and_market_state": result,
            "governance": "DESCRIPTIVE_RESEARCH_ONLY"}


def build_market_context(context_charts, share_series, *, evaluated_at):
    """ETF prices are benchmarks only; sampled share breadth is not a JSE index."""
    now = timestamp(evaluated_at.isoformat() if hasattr(evaluated_at, "isoformat")
                    else evaluated_at)
    benchmarks = {}
    for key in CONTEXT_ETFS:
        expected = MARKET_CHART_INSTRUMENTS[key].data_symbol
        chart = context_charts.get(key)
        if chart and chart.get("symbol") == expected:
            movement = _etf_momentum(chart, now)
            if movement is not None:
                benchmarks[key] = movement
    market = benchmarks.get("ETF_STX40")
    movements = [values[-1][1] / values[-21][1] - 1
                 for values in share_series.values() if len(values) >= 21
                 and values[-21][1] > 0 and
                 (market is None or values[-1][0].isoformat() == market["session_at"])]
    breadth = sum(value > 0 for value in movements) / len(movements) if movements else None
    # A market classification needs both the independently listed ETF and a
    # non-trivial cross-section of available cash-share observations.
    if market is None or len(movements) < 6:
        state = "INSUFFICIENT_CONTEXT"
    elif market["return_20_sessions"] > 0 and breadth >= .55:
        state = "SUPPORTIVE"
    elif market["return_20_sessions"] < 0 and breadth <= .45:
        state = "DEFENSIVE"
    else:
        state = "MIXED"
    return {"version": VERSION, "evaluated_at": now.isoformat(),
            "state": state, "sampled_share_count": len(movements),
            "sampled_share_breadth_20_sessions": breadth,
            "benchmarks": benchmarks, "basis": "LISTED_ETF_PRICES_AND_SAMPLED_CASH_SHARE_BREADTH",
            "limitations": "Delayed closes; ETF prices are context, not admitted trade candidates"}


def build_decision_brief(opportunities, share_series, market_context, *, available_cash,
                         open_instruments=(), evaluated_at, benchmark_learning=None, strategy_profile=None):
    """Prioritise human review; never turn delayed closes into an order."""
    now = timestamp(evaluated_at.isoformat() if hasattr(evaluated_at, "isoformat")
                    else evaluated_at)
    catalog = public_share_catalog()
    by_instrument = {value["instrument_id"]: key for key, value in share_series.items()}
    ideas = []
    for opportunity in opportunities:
        same_strategy(opportunity, strategy_profile)
        if opportunity.rank is None or opportunity.rank > 5:
            continue
        key = by_instrument.get(opportunity.instrument_id)
        values = share_series.get(key, {}).get("bars", ()) if key else ()
        if not values:
            continue
        bar_at, price, _ = values[-1]
        sector = catalog[key].get("sector", "Unclassified")
        if opportunity.direction != "LONG" or opportunity.eligibility_status != "ELIGIBLE":
            state, reason = "NOT_ADMITTED", "No eligible fully funded LONG idea"
        elif opportunity.instrument_id in open_instruments:
            state, reason = "ALREADY_HELD", "Already present in the paper book"
        elif market_context["state"] == "DEFENSIVE":
            state, reason = "WAIT_MARKET", "ETF benchmark and sampled breadth are both weak"
        elif market_context["state"] == "INSUFFICIENT_CONTEXT":
            state, reason = "WAIT_CONTEXT", "Broad-market context is incomplete"
        elif price > available_cash:
            state, reason = "PAPER_CASH_LIMIT", "One share exceeds available simulated cash"
        else:
            state, reason = "REVIEW", "Check current quote, spread, total costs and risk before any manual decision"
        ideas.append({**fields(opportunity), "instrument_id": opportunity.instrument_id, "symbol": key,
                      "sector": sector, "rank": opportunity.rank,
                      "legacy_ranking_score": opportunity.ranking_score,
                      "state": state, "reason": reason, "last_completed_close": price,
                      "last_completed_bar_at": bar_at.isoformat(),
                      "minimum_one_share_notional": price})
    return {**fields(strategy_profile), "version": VERSION, "evaluated_at": now.isoformat(),
            "market": market_context, "ideas": ideas[:5],
            "benchmark_learning": benchmark_learning or {},
            "simulated_available_cash": available_cash,
            "action_boundary": "RESEARCH_ONLY; DELAYED_PRICE; HUMAN_VERIFICATION_REQUIRED",
            "legacy_benchmark_preserved": True, "live_execution": False}
