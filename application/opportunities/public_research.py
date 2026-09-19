"""Bounded public cash-share research inputs for the existing canonical ranker.

The curated Yahoo/JSE catalog supplies identities, never broker contracts.  A
daily close becomes usable at the following UTC midnight; only matured next-bar
outcomes can contribute to M11 effectiveness.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from math import isfinite

from domain.evaluation.effectiveness import ContextualEffectivenessLearner, FeatureOutcome
from domain.evaluation.opportunity import OpportunityCandidate, rank_opportunities
from domain.evaluation.suitability import CostEvidence, LiquidityEvidence, SuitabilityEvidence, evaluate_suitability
from domain.features.divergence import DivergenceConfig, SignalEvidence, summarize
from domain.features.regime import RegimeParameters, classify_candidate
from domain.registry.instrument import CanonicalInstrument, DEFAULT_INSTRUMENT_REGISTRY, GovernanceState
from indicator_effectiveness import signal_outcome
from intraday_instruments import DataGrade, InstrumentDefinition
from jse_adapter import JSE_TICKERS, YahooFinanceFetcher

VERSION = "public-cash-research-v1"
COST_BPS = 10.0  # Declared research assumption: 5 spread + 2 fees + 3 slippage.


def persisted_shadow_evidence(repository, *, evaluated_at):
    """Return only matured persisted shadow aggregates keyed by canonical ID."""
    from shadow_learning import timestamp
    result = {}
    for item in repository.list_adaptive_evidence():
        try:
            updated = timestamp(item.get("updated_at", ""))
        except (TypeError, ValueError):
            continue
        if updated > evaluated_at:
            continue
        instrument = str(item.get("instrument", "")).upper()
        result[instrument] = {**item, "state": "PERSISTED_MATURED"}
    return result


def public_share_catalog():
    """Only curated cash shares with a JSE Yahoo mapping can enter this universe."""
    return {key: data for key, data in JSE_TICKERS.items()
            if isinstance(data.get("yahoo_symbol"), str)
            and data["yahoo_symbol"].endswith(".JO")
            and data.get("name")}


def public_share_list():
    return [{"instrument_id": key, "display_symbol": data["yahoo_symbol"].removesuffix(".JO"), "name": data["name"],
             "sector": data.get("sector", "unspecified"), "yahoo_symbol": data["yahoo_symbol"],
             "capabilities": {"public_chart": True, "operational_analysis": _legacy(key),
                              "broker_execution": False}}
            for key, data in public_share_catalog().items()]


def _legacy(key):
    from instrument_registry import resolve_instrument
    try:
        resolve_instrument(key)
        return True
    except KeyError:
        return False


def _identities(key, data):
    try:
        canonical = DEFAULT_INSTRUMENT_REGISTRY.resolve(key)
    except KeyError:
        canonical = CanonicalInstrument(
            f"EQ_ZAR_{key}", data["name"], "equity", key, key,
            data["yahoo_symbol"], None, "XJSE", "ZAR", "Africa/Johannesburg",
            "JSE", None, None, None, None, None, None,
            GovernanceState.RESEARCH, (key, data["yahoo_symbol"]), ("1d",),
            ("yahoo", "historical"), "jse_adapter.JSE_TICKERS", "cash_equity",
            data.get("sector", "unspecified"))
    research = InstrumentDefinition(
        canonical.instrument_id, data["name"], key, key, "equity", "cash_equity",
        "ZAR", "single_stock_neutral", data_symbol=data["yahoo_symbol"],
        exchange="XJSE", timezone="Africa/Johannesburg", supports_intraday=False,
        supports_historical_data=True, data_grade=DataGrade.RESEARCH,
        data_status="DELAYED_PUBLIC", sector=data.get("sector", "unspecified"))
    return canonical, research


def _available_at(stamp):
    date = datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()
    return datetime(date.year, date.month, date.day, tzinfo=timezone.utc) + timedelta(days=1)


def _signal(closes, feature):
    if feature == "momentum_20d":
        difference = closes[-1] - closes[-21]
        return 1 if difference > 0 else -1 if difference < 0 else 0
    from opportunity_scanner import _rsi
    value = _rsi(closes)
    return 1 if value is not None and value < 30 else -1 if value is not None and value > 70 else 0


def candidate_from_chart(key, chart, *, evaluated_at, news_report=None, learned_evidence=None):
    catalog = public_share_catalog()
    if key not in catalog:
        raise ValueError("share is outside the curated public catalog")
    data = catalog[key]
    if chart.get("symbol") != data["yahoo_symbol"] or chart.get("interval") != "1d" or chart.get("currency") != "ZAR":
        raise ValueError("public daily chart identity, interval or currency mismatch")
    rows = chart.get("bars") or []
    if len(rows) > 400:
        rows = rows[-400:]
    bars = [(row["timestamp"], float(row["close"])) for row in rows]
    if any(not isfinite(close) or close <= 0 for _, close in bars):
        raise ValueError("invalid public close")
    clocks = [_available_at(stamp) for stamp, _ in bars]
    if any(left >= right for left, right in zip(clocks, clocks[1:])):
        raise ValueError("daily bars must have unique increasing dates")
    available = [(clock, close) for clock, (_, close) in zip(clocks, bars) if clock <= evaluated_at]
    if not available or evaluated_at - available[-1][0] > timedelta(days=7):
        raise ValueError("public chart is stale or unavailable")
    clocks, closes = zip(*available)
    canonical, research = _identities(key, data)
    learner = ContextualEffectivenessLearner()
    evidence = []
    signals = []
    for feature in ("momentum_20d", "rsi_14"):
        outcomes = []
        previous = 0
        for i in range(20, len(closes) - 1):
            state = _signal(closes[:i + 1], feature)
            if state:
                forward = closes[i + 1] / closes[i] - 1
                gross, _, net = signal_outcome(state, previous, forward, COST_BPS)
                outcomes.append(FeatureOutcome(
                    feature, VERSION, "technical", canonical.instrument_id, "1d", None,
                    None, state, clocks[i], clocks[i], clocks[i + 1], gross, net,
                    f"{key}:{feature}:{clocks[i].date().isoformat()}"))
            previous = state
        evidence.append(learner.estimate(
            outcomes, feature_id=feature, evaluated_at=evaluated_at,
            instrument_id=canonical.instrument_id, horizon_id="1d"))
        if len(closes) >= 21:
            signals.append(SignalEvidence(feature, VERSION, _signal(closes, feature),
                                          clocks[-1], instrument_id=canonical.instrument_id,
                                          horizon_id="1d", category="technical"))
    effectiveness = tuple(evidence)
    regime = classify_candidate(
        closes, evaluated_at, RegimeParameters(.02, .025, .008),
        available_times=clocks,
        macro_risk=((news_report or {}).get("macro_risk") or "UNKNOWN"),
    )
    ticker_news = ((news_report or {}).get("tickers") or {}).get(key)
    macro = (news_report or {}).get("macro") or {}
    input_evidence = {
        "technical": {
            "features": ("momentum_20d", "rsi_14"),
            "last_available_at": clocks[-1].isoformat(),
            "momentum_20d_signal": _signal(closes, "momentum_20d"),
            "rsi_14_signal": _signal(closes, "rsi_14"),
        },
        "regime": regime.to_dict(),
        "news_macro": {
            "state": "AVAILABLE" if ticker_news or macro else "UNAVAILABLE",
            "ticker": ticker_news,
            "macro": macro,
            "evaluated_at": evaluated_at.isoformat(),
        },
        "learned_effectiveness": dict((learned_evidence or {}).get(canonical.instrument_id, {
            "state": "UNAVAILABLE",
            "reason": "NO_PERSISTED_SHADOW_EVIDENCE",
        })),
    }
    suitability = evaluate_suitability(
        research, "1d", evaluated_at,
        data=SuitabilityEvidence("AVAILABLE", DataGrade.RESEARCH, "Yahoo public daily bars",
                                 "1d", len(closes), 0.0, "NEXT_DAY_BAR_AVAILABILITY",
                                 f"{clocks[0].date()}/{clocks[-1].date()}"),
        features=effectiveness, costs=CostEvidence("ASSUMED", COST_BPS, "5+2+3 bps research assumption"),
        liquidity=LiquidityEvidence("UNKNOWN"), provenance={
            "catalog": "jse_adapter.JSE_TICKERS", "data_symbol": data["yahoo_symbol"],
            "last_usable_session": (clocks[-1] - timedelta(days=1)).date().isoformat(),
            "research_pipeline": VERSION, "cost_assumption_bps": COST_BPS})
    divergence = summarize(signals, evaluated_at, DivergenceConfig(2, 1),
                           instrument_id=canonical.instrument_id, horizon_id="1d")
    return OpportunityCandidate(canonical, suitability, divergence, effectiveness,
                                regime, DataGrade.RESEARCH.value,
                                input_evidence=input_evidence)


@dataclass(frozen=True)
class RefreshResult:
    opportunities: tuple
    unavailable: tuple
    scanned: int


def refresh_public_research(*, fetcher=None, evaluated_at=None, universe=None, max_workers=4,
                            news_report=None, learned_evidence=None):
    """One bounded on-demand pass. Failed shares never become ranked records."""
    evaluated_at = evaluated_at or datetime.now(timezone.utc)
    catalog = public_share_catalog()
    keys = tuple(key for key in (universe or catalog) if key in catalog)[:30]
    fetcher = fetcher or YahooFinanceFetcher()
    candidates, unavailable = [], []

    def load(key):
        return candidate_from_chart(key, fetcher.get_chart(catalog[key]["yahoo_symbol"], "1y"),
                                    evaluated_at=evaluated_at, news_report=news_report,
                                    learned_evidence=learned_evidence)

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="public-research") as pool:
        futures = {pool.submit(load, key): key for key in keys}
        for future in as_completed(futures):
            key = futures[future]
            try:
                candidates.append(future.result())
            except (ValueError, KeyError, TypeError, IndexError, OverflowError):
                unavailable.append({"symbol": key, "reason": "PUBLIC_DATA_OR_EVIDENCE_UNAVAILABLE"})
            except Exception:
                unavailable.append({"symbol": key, "reason": "PUBLIC_PROVIDER_UNAVAILABLE"})
    ranked = rank_opportunities(candidates, evaluated_at=evaluated_at, top_n=5)
    lineage = {item.instrument.instrument_id: item.suitability.provenance for item in candidates}
    opportunities = tuple(replace(item, provenance={**item.provenance,
                           **lineage[item.instrument_id]}) for item in ranked.opportunities)
    return RefreshResult(opportunities, tuple(sorted(unavailable, key=lambda x: x["symbol"])), len(keys))
