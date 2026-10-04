"""Host composition for the shared web/worker PAPER account."""
from dataclasses import asdict
from datetime import datetime, timezone
import os
from .paper_config import PaperLoopConfig
from .paper_loop import PaperLoop, opportunity_from_dict, paper_feature_outcomes
from .daily_learning import candidate_panel_summary
from .market_brief import CONTEXT_ETFS
from .service import OpportunityService
from .public_research import public_share_catalog, _available_at
from domain.broker.paper import PaperBroker
from shadow_learning import stable_id, timestamp
from workers.paper_loop import PaperScheduler, FrozenPaperHandler
from domain.strategy import DEFAULT_STRATEGY_REGISTRY
from domain.strategy.attribution import fields, reference


FROZEN_HISTORY_BARS = 60


def completed_session_identity(charts, cutoff):
    """Identify the causally usable source sessions without retaining bar data."""
    sessions = {}
    for key, chart in charts.items():
        try:
            usable = [bar for bar in chart.get("bars", ())
                      if _available_at(bar["timestamp"]) <= cutoff]
            if usable:
                sessions[key] = usable[-1]["timestamp"]
        except (KeyError, TypeError, ValueError):
            continue
    if not sessions:
        return None, sessions
    ordered = tuple(sorted(sessions.items()))
    return stable_id("paper-completed-sessions", *ordered), sessions


def configured_paper():
    path = os.environ.get("PAPER_LOOP_CONFIG")
    return PaperLoopConfig.load(path) if path else None


def persisted_news(repository, now):
    """Bounded reuse of normalized, policy-enabled evidence. No new collector."""
    items, seen_articles = [], set()
    rows = repository._job_sql(
        "SELECT evidence_id FROM evidence_records ORDER BY ingested_at DESC,evidence_id LIMIT 100", rows=True)
    for (eid,) in rows:
        evidence = repository.get_evidence(eid)
        policy = repository.get_source_policy(evidence.source_id)
        if not policy or not policy.enabled or policy.governance_state.value in {"DISABLED", "BLOCKED"}:
            continue
        try:
            available = max(timestamp(evidence.ingested_at), timestamp(evidence.observed_at))
            published = timestamp(evidence.published_at or evidence.observed_at)
        except (TypeError, ValueError):
            continue
        if not published <= available <= now or (now-available).total_seconds() > 86400:
            continue
        article = evidence.metadata.get("article_id", eid)
        if article in seen_articles:
            continue
        seen_articles.add(article)
        items.append({"evidence_id": eid, "source": evidence.source_name,
                      "timestamp": published.isoformat(), "available_at": available.isoformat(),
                      "url": evidence.url, "score": evidence.score,
                      "assets": [{"name": x} for x in evidence.tickers],
                      "macro_assets": list(evidence.assets), "parser_version": evidence.parser_version,
                      "llm_used": evidence.metadata.get("llm_used", False),
                      "analysis_provider": evidence.metadata.get("analysis_provider"),
                      "analysis_model": evidence.metadata.get("analysis_model")})
    return {"available_at": now.isoformat(), "items": items}


def compose_paper_worker(repository, config, *, fetcher=None, clock=None, strategy_profile=None):
    from jse_adapter import YahooFinanceFetcher
    clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
    fetcher = fetcher or YahooFinanceFetcher()
    loop = PaperLoop(repository, config)
    loop.initialize()
    profile = strategy_profile or DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d", "1.0.1")
    if profile.strategy_family != "jse_cash_swing" or profile.canonical_workflow_tab != "canonical-opportunities":
        raise ValueError("only the existing Swing paper workflow may be attributed")
    scheduler = PaperScheduler(repository, config.account_id, interval_seconds=config.interval_seconds,
                               strategy_profile=profile)
    from domain.strategy.attribution import freeze_profile
    technical_definition = freeze_profile(DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d", "1.1.0"))
    from .swing_policy import frozen_definition
    policy_definition = frozen_definition()
    scanner = None
    if os.environ.get("PAPER_NEWS_ENABLED") == "1":
        from sentiment_analyzer import MacroSentimentScanner
        scanner = MacroSentimentScanner(max_llm_items=2, retain_items=True)

    def loader():
        observed_at = timestamp(clock())
        charts, acquired = {}, {}
        for key in config.universe:
            try:
                chart = fetcher.get_chart(public_share_catalog()[key]["yahoo_symbol"], "1y")
                if chart.get("symbol") != public_share_catalog()[key]["yahoo_symbol"]:
                    continue
                acquired[key] = chart
                charts[key] = {name: chart[name] for name in ("symbol", "currency", "interval")}
                charts[key]["bars"] = [
                    {**{name: bar.get(name) for name in ("timestamp", "close", "volume")},
                     **{name: bar[name] for name in ("open", "high", "low") if bar.get(name) is not None}}
                    for bar in chart["bars"][-FROZEN_HISTORY_BARS:]
                ]
            except Exception:
                # Missing data is visible per symbol; exception text can include secrets.
                continue
        if scanner is not None:
            from .news_ingestion import persist_news_report
            # Provider failure must not manufacture evidence or prevent position management.
            try:
                report = scanner.scan(moneyweb_limit=20, sens_limit=15).to_dict()
                persist_news_report(repository, report, observed_at=clock())
            except Exception:
                pass
        context_charts, acquired_context = {}, {}
        from market_chart_registry import MARKET_CHART_INSTRUMENTS
        for key in CONTEXT_ETFS:
            try:
                chart = fetcher.get_chart(MARKET_CHART_INSTRUMENTS[key].data_symbol, "1y")
                if chart.get("symbol") != MARKET_CHART_INSTRUMENTS[key].data_symbol:
                    continue
                acquired_context[key] = chart
                context_charts[key] = {name: chart[name] for name in ("symbol", "currency", "interval")}
                context_charts[key]["bars"] = [
                    {**{name: bar.get(name) for name in ("timestamp", "close", "volume")},
                     **{name: bar[name] for name in ("open", "high", "low") if bar.get(name) is not None}}
                    for bar in chart["bars"][-FROZEN_HISTORY_BARS:]
                ]
            except Exception:
                continue
        source_signature, sessions = completed_session_identity({**charts, **context_charts}, observed_at)
        state = repository.paper_account(config.account_id) or {}
        if source_signature and source_signature == state.get("last_source_signature"):
            return {"state": "NO_NEW_COMPLETED_SESSION", "duplicate_session": True,
                    "source_signature": source_signature, "completed_sessions": sessions}
        from .swing_history import BENCHMARK, current_evidence, load_report
        history = load_report()
        swing_evidence = {key: current_evidence(key, chart, context_charts.get(BENCHMARK),
                         evaluated_at=observed_at, report=history)
                         for key, chart in {**charts, **context_charts}.items()}
        from .swing_technical import snapshot as swing_snapshot
        from .alpha_vantage_data import configured_client, repair_chart
        shadow_acquired = {**acquired, **acquired_context}
        alpha_report = {"state": "NOT_CONFIGURED", "live_execution": False, "instruments": {}}
        try:
            alpha = configured_client(repository)
        except Exception:
            alpha = None
            alpha_report["state"] = "CONFIGURATION_UNAVAILABLE"
        if alpha is not None:
            alpha_report["state"] = "YAHOO_FIRST_CONDITIONAL_FALLBACK"
            for key in alpha.ordered_keys(shadow_acquired):
                chart = shadow_acquired[key]
                try:
                    shadow_acquired[key], alpha_report["instruments"][key] = repair_chart(alpha, chart, observed_at)
                except Exception:
                    alpha_report["instruments"][key] = {"state": "REPAIR_UNAVAILABLE"}
        shadow_input = {}
        if any(row.get("repaired_sessions") for row in alpha_report["instruments"].values()):
            shadow_input["swing_charts"] = {key: {**chart, "bars": chart["bars"][-FROZEN_HISTORY_BARS:]}
                                           for key, chart in shadow_acquired.items()}
        from .ig_swing_data import configured_investigation
        ig_swing_data = configured_investigation(config.universe, observed_at)
        swing_technical = {key: {**swing_snapshot(chart, evaluated_at=observed_at,
            benchmark_chart=shadow_acquired.get(BENCHMARK)),
            **({"data_repair": alpha_report["instruments"][key]} if key in alpha_report["instruments"] else {})}
            for key, chart in shadow_acquired.items()}
        return {"charts": charts, "context_charts": context_charts,
                "swing_technical": swing_technical,
                "swing_technical_definition": technical_definition,
                "swing_policy_definition": policy_definition,
                "ig_swing_data": ig_swing_data,
                **shadow_input,
                "alpha_vantage_data": alpha_report,
                "swing_history_evidence": swing_evidence,
                "news": persisted_news(repository, observed_at),
                "source_signature": source_signature, "completed_sessions": sessions}

    def processor(key, frozen):
        if frozen["input"].get("duplicate_session"):
            return {"mode": "PAPER", "live_execution": False,
                    **fields(frozen),
                    "evaluated_at": frozen["evaluated_at"],
                    "state": "NO_NEW_COMPLETED_SESSION",
                    "source_signature": frozen["input"]["source_signature"]}
        return loop.cycle(key, frozen, paused=os.environ.get("PAPER_PAUSED") == "1")

    return scheduler, FrozenPaperHandler(repository, config.account_id, loader, processor, clock)


class DurablePaperOpportunities(OpportunityService):
    """The configured web process reads the worker's committed ranking only."""
    def __init__(self, repository_factory, config, clock=None):
        super().__init__()
        self.factory, self.config = repository_factory, config
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _read(self, asset_class="cash_equity"):
        repository = self.factory()
        try:
            state = repository.paper_account(self.config.account_id)
            if not state or not state["ranking_record_id"]:
                return ()
            snapshot = repository.paper_record(state["ranking_record_id"])
            at = timestamp(snapshot["evaluated_at"])
            now = self.clock()
            if at > now or (now-at).total_seconds() > self.config.max_price_age_seconds:
                return ()
            rows = snapshot.get("etf_opportunities", ()) if asset_class == "index_etf" else snapshot["opportunities"]
            if asset_class == "all":
                rows = [*snapshot["opportunities"], *snapshot.get("etf_opportunities", ())]
            return tuple(opportunity_from_dict(row) for row in rows
                         if row["rank"] is not None or row["instrument_id"].startswith("ETF_"))
        finally:
            repository.close()

    def list_opportunities(self, limit=None, *, asset_class="cash_equity"):
        if asset_class not in {"cash_equity", "index_etf"}:
            raise ValueError("unsupported research asset class")
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("limit must be a positive integer")
        values = sorted(self._read(asset_class), key=lambda x: (x.rank if x.rank is not None else 999, x.opportunity_id))
        return tuple(values[:limit] if limit else values)

    def get_opportunity(self, oid):
        # Never use a stale in-process copy when the database is unavailable.
        return {x.opportunity_id: x for x in self._read("all")}[oid]


class PaperRefreshStatus:
    def __init__(self, repository_factory, config):
        self.factory, self.config = repository_factory, config

    def status(self):
        repository = self.factory()
        try:
            state = repository.paper_account(self.config.account_id)
            snapshot = repository.paper_record(state["ranking_record_id"]) if state and state["ranking_record_id"] else None
            at = timestamp(snapshot["evaluated_at"]) if snapshot else None
            now = datetime.now(timezone.utc)
            stale = at is not None and (at > now or (now-at).total_seconds() > self.config.max_price_age_seconds)
            status = _paper_state(state, snapshot, stale)
            return {"state": status, "running": False,
                    "last_completed": state["last_evaluated_at"] if state else None,
                    "scanned": len(self.config.universe) if snapshot else 0,
                    "unranked": sum(row["rank"] is None for row in snapshot["opportunities"]) if snapshot else 0,
                    "unavailable": snapshot["unavailable"] if snapshot else list(self.config.universe),
                    "etf_research": snapshot.get("etf_research") if snapshot else None,
                    "source": "DURABLE_PAPER_WORKER"}
        finally:
            repository.close()

    def trigger(self):
        # HTTP refresh is read-only. The worker owns the schedule and all mutations.
        return self.status()


def paper_status(repository, config):
    state = repository.paper_account(config.account_id)
    if state is None:
        return {"state": "WORKER_NOT_STARTED", "mode": "PAPER", "live_execution": False}
    now = datetime.now(timezone.utc)
    at = timestamp(state["last_evaluated_at"]) if state["last_evaluated_at"] else None
    stale = at is None or at > now or (now-at).total_seconds() > config.max_price_age_seconds
    snapshot = (repository.paper_record(state["ranking_record_id"])
                if state.get("ranking_record_id") else None)
    strategy = reference(snapshot)
    from .paper_controls import controls_for, AGGRESSION
    controls = controls_for(state, config)
    cutoff = now.isoformat()
    totals = dict(repository._job_sql("SELECT kind,COUNT(*) FROM paper_records WHERE account_id=? AND available_at<=? GROUP BY kind",
                                     (config.account_id, cutoff), rows=True))
    cycles = repository.paper_records(config.account_id, "cycle", as_of=cutoff, limit=96)
    outcomes = repository.paper_records(config.account_id, "outcome", as_of=cutoff, limit=400)
    learning_outcomes = repository.paper_records(
        config.account_id, "learning-outcome", as_of=cutoff, limit=1000)
    panel_summary = (snapshot.get("candidate_learning") if snapshot else None) or \
        candidate_panel_summary(repository, config.account_id, evaluated_at=now,
            strategy_profile=strategy, horizon_sessions=config.learning_horizon_sessions)
    from domain.evaluation.effectiveness import ContextualEffectivenessLearner
    strategy_outcomes = paper_feature_outcomes(repository, config.account_id, now,
        horizon_sessions=config.holding_sessions, strategy_profile=strategy)
    estimates = [ContextualEffectivenessLearner().estimate(strategy_outcomes,
        feature_id="paper_strategy", evaluated_at=now, instrument_id=instrument,
        horizon_id=("1d" if config.holding_sessions == 1 else f"{config.holding_sessions}_sessions"),
        strategy_profile=strategy) for instrument in sorted({row.instrument_id for row in strategy_outcomes})]
    strategy_learning = {**fields(strategy), "strategy_attribution_state": "ATTRIBUTED" if strategy else "LEGACY_UNATTRIBUTED",
        "eligible_closed_outcomes": len(strategy_outcomes), "holding_sessions": config.holding_sessions,
        "minimum_sample": 30, "read_limit": 400, "governance": "RESEARCH_ONLY_NOT_PROMOTION",
        "cost_basis": "SIMULATED_FILL_COSTS_NOT_ACTUAL_OST_FEES",
        "cells": [{"instrument_id": row.instrument_id, "horizon_id": row.horizon_id,
                   "status": row.status, "sample_count": row.sample_count, "negative_outcomes": row.negative_outcomes,
                   "expected_return_net": row.expected_return_net, "uncertainty": row.uncertainty,
                   "fallback_level": row.fallback_level} for row in estimates]}
    scope = ("s.strategy_profile_id=? AND s.strategy_profile_version=?" if strategy else "s.record_id IS NULL")
    decision_count = repository._job_sql("SELECT COUNT(*) FROM paper_records p LEFT JOIN strategy_record_refs s ON p.record_id=s.record_id "
        "WHERE p.account_id=? AND p.kind='candidate-decision' AND p.available_at<=? AND " + scope,
        (config.account_id, cutoff, *([strategy.strategy_profile_id, strategy.strategy_profile_version] if strategy else [])), rows=True)[0][0]
    counts = {}
    for outcome in learning_outcomes:
        if outcome.get("horizon_sessions") == config.learning_horizon_sessions:
            key = outcome["instrument_id"]
            counts[key] = counts.get(key, 0) + 1
    proposed = [{"instrument_id": row["opportunity"]["instrument_id"],
                 **fields(row["opportunity"]),
                 "direction": row["opportunity"]["direction"],
                 "rank": row["opportunity"]["rank"], "evaluated_at": row["opportunity"]["evaluated_at"],
                 "state": "PAUSED" if controls["paused"] else "SHORT_BORROW_UNAVAILABLE" if row["opportunity"]["direction"] == "SHORT" else "WAITING_FOR_NEXT_COMPLETE_SESSION"}
                for row in state["pending"]]
    evidence_count = repository._job_sql(
        "SELECT COUNT(*) FROM evidence_records WHERE parser_version=? AND ingested_at<=?",
        ("persisted-public-analysis-v1", cutoff), rows=True)[0][0]
    return {"state": _paper_state(state, snapshot, stale), "mode": "PAPER", "live_execution": False,
            **fields(strategy), "strategy_attribution_state": "ATTRIBUTED" if strategy else "LEGACY_UNATTRIBUTED",
            "account_id": config.account_id, "last_evaluated_at": state["last_evaluated_at"],
            "controls": controls, "effective_risk_fraction": config.risk_fraction * AGGRESSION[controls["aggression"]],
            "risk_limits": config.limits, "model": "Daily close · ZAR cash shares · long only",
            "data_provider": "Yahoo Finance", "interval_seconds": config.interval_seconds,
            "commission_per_fill": config.commission_per_fill, "slippage_per_unit": config.slippage_per_unit,
            "pending": proposed, "position_geometry": state["book"], "totals": totals,
            "learning": {"outcomes_by_instrument": counts, "minimum_samples": 30,
                         "horizon_sessions": config.learning_horizon_sessions,
                         "eligible_outcomes": sum(counts.values()), "persisted_news_records": evidence_count,
                         "state": "LEARNED_CELLS_AVAILABLE" if any(n >= 30 for n in counts.values()) else "COLLECTING_OUTCOMES",
                         "kind": "Legacy selected-only v1 outcomes; no automatic candidate learning"},
            "candidate_learning": {**panel_summary,
                                   "decision_count": decision_count},
            "strategy_learning": strategy_learning,
            "swing_technical_learning": snapshot.get("swing_technical_learning") if snapshot else None,
            "swing_policy_shadow": snapshot.get("swing_policy_shadow") if snapshot else None,
            "ig_swing_data": snapshot.get("ig_swing_data") if snapshot else None,
            "alpha_vantage_data": snapshot.get("alpha_vantage_data") if snapshot else None,
            "swing_technical": snapshot.get("swing_technical") if snapshot else None,
            "decision_brief": snapshot.get("decision_brief") if snapshot else None,
            "etf_research": snapshot.get("etf_research") if snapshot else None,
            "equity_history": [{"at": row["evaluated_at"], "equity": row["account"]["equity"]} for row in reversed(cycles)],
            "account": asdict(PaperBroker.restore(state["broker"]).get_account()),
            "positions": state["broker"]["positions"],
            "recent_cycles": cycles[:5], "recent_outcomes": outcomes[:10],
            "recent_fills": repository.paper_records(config.account_id, "fill", as_of=cutoff, limit=20),
            "recent_policies": repository.paper_records(config.account_id, "policy", as_of=cutoff, limit=10),
            "recent_risks": repository.paper_records(config.account_id, "risk", as_of=cutoff, limit=10)}


def _paper_state(state, snapshot, stale):
    if state is None:
        return "WORKER_NOT_STARTED"
    if stale:
        return "STALE"
    if snapshot and not snapshot.get("opportunities") and snapshot.get("unavailable"):
        return "NO_USABLE_MARKET_DATA"
    return state["status"]
