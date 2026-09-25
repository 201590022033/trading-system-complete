"""Host composition for the shared web/worker PAPER account."""
from dataclasses import asdict
from datetime import datetime, timezone
import os
from .paper_config import PaperLoopConfig
from .paper_loop import PaperLoop, opportunity_from_dict
from .service import OpportunityService
from .public_research import public_share_catalog
from domain.broker.paper import PaperBroker
from shadow_learning import timestamp
from workers.paper_loop import PaperScheduler, FrozenPaperHandler


FROZEN_HISTORY_BARS = 60


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


def compose_paper_worker(repository, config, *, fetcher=None, clock=None):
    from jse_adapter import YahooFinanceFetcher
    clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
    fetcher = fetcher or YahooFinanceFetcher()
    loop = PaperLoop(repository, config)
    loop.initialize()
    scheduler = PaperScheduler(repository, config.account_id, interval_seconds=config.interval_seconds)
    scanner = None
    if os.environ.get("PAPER_NEWS_ENABLED") == "1":
        from sentiment_analyzer import MacroSentimentScanner
        scanner = MacroSentimentScanner(max_llm_items=2, retain_items=True)

    def loader():
        charts = {}
        for key in config.universe:
            try:
                chart = fetcher.get_chart(public_share_catalog()[key]["yahoo_symbol"], "1y")
                charts[key] = {name: chart[name] for name in ("symbol", "currency", "interval")}
                charts[key]["bars"] = [
                    {name: bar.get(name) for name in ("timestamp", "close", "volume")}
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
        return {"charts": charts, "news": persisted_news(repository, timestamp(clock()))}

    def processor(key, frozen):
        return loop.cycle(key, frozen, paused=os.environ.get("PAPER_PAUSED") == "1")

    return scheduler, FrozenPaperHandler(repository, config.account_id, loader, processor, clock)


class DurablePaperOpportunities(OpportunityService):
    """The configured web process reads the worker's committed ranking only."""
    def __init__(self, repository_factory, config, clock=None):
        super().__init__()
        self.factory, self.config = repository_factory, config
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _read(self):
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
            return tuple(opportunity_from_dict(row) for row in snapshot["opportunities"] if row["rank"] is not None)
        finally:
            repository.close()

    def list_opportunities(self, limit=None):
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("limit must be a positive integer")
        values = sorted(self._read(), key=lambda x: (x.rank, x.opportunity_id))
        return tuple(values[:limit] if limit else values)

    def get_opportunity(self, oid):
        # Never use a stale in-process copy when the database is unavailable.
        return {x.opportunity_id: x for x in self._read()}[oid]


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
            return {"state": "STALE" if stale else state["status"] if state else "WORKER_NOT_STARTED", "running": False,
                    "last_completed": state["last_evaluated_at"] if state else None,
                    "scanned": len(self.config.universe) if snapshot else 0,
                    "unranked": sum(row["rank"] is None for row in snapshot["opportunities"]) if snapshot else 0,
                    "unavailable": snapshot["unavailable"] if snapshot else list(self.config.universe),
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
    from .paper_controls import controls_for, AGGRESSION
    controls = controls_for(state, config)
    cutoff = now.isoformat()
    totals = dict(repository._job_sql("SELECT kind,COUNT(*) FROM paper_records WHERE account_id=? AND available_at<=? GROUP BY kind",
                                     (config.account_id, cutoff), rows=True))
    cycles = repository.paper_records(config.account_id, "cycle", as_of=cutoff, limit=96)
    outcomes = repository.paper_records(config.account_id, "outcome", as_of=cutoff, limit=400)
    learning_outcomes = repository.paper_records(
        config.account_id, "learning-outcome", as_of=cutoff, limit=1000)
    counts = {}
    for outcome in learning_outcomes:
        if outcome.get("horizon_sessions") == config.learning_horizon_sessions:
            key = outcome["instrument_id"]
            counts[key] = counts.get(key, 0) + 1
    proposed = [{"instrument_id": row["opportunity"]["instrument_id"],
                 "direction": row["opportunity"]["direction"],
                 "rank": row["opportunity"]["rank"], "evaluated_at": row["opportunity"]["evaluated_at"],
                 "state": "PAUSED" if controls["paused"] else "SHORT_BORROW_UNAVAILABLE" if row["opportunity"]["direction"] == "SHORT" else "WAITING_FOR_NEXT_COMPLETE_SESSION"}
                for row in state["pending"]]
    evidence_count = repository._job_sql(
        "SELECT COUNT(*) FROM evidence_records WHERE parser_version=? AND ingested_at<=?",
        ("persisted-public-analysis-v1", cutoff), rows=True)[0][0]
    return {"state": "STALE" if stale else state["status"], "mode": "PAPER", "live_execution": False,
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
                         "kind": "Ranked LONG swing effectiveness after declared costs; LLM model weights are not trained"},
            "equity_history": [{"at": row["evaluated_at"], "equity": row["account"]["equity"]} for row in reversed(cycles)],
            "account": asdict(PaperBroker.restore(state["broker"]).get_account()),
            "positions": state["broker"]["positions"],
            "recent_cycles": cycles[:5], "recent_outcomes": outcomes[:10],
            "recent_fills": repository.paper_records(config.account_id, "fill", as_of=cutoff, limit=20),
            "recent_policies": repository.paper_records(config.account_id, "policy", as_of=cutoff, limit=10),
            "recent_risks": repository.paper_records(config.account_id, "risk", as_of=cutoff, limit=10)}
