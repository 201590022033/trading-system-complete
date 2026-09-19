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


def configured_paper():
    path = os.environ.get("PAPER_LOOP_CONFIG")
    return PaperLoopConfig.load(path) if path else None


def persisted_news(repository, now):
    """Bounded reuse of normalized, policy-enabled evidence. No new collector."""
    items = []
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
        items.append({"evidence_id": eid, "source": evidence.source_name,
                      "timestamp": published.isoformat(), "available_at": available.isoformat(),
                      "url": evidence.url, "score": evidence.score,
                      "assets": [{"name": x} for x in evidence.tickers],
                      "macro_assets": list(evidence.assets), "parser_version": evidence.parser_version})
    return {"available_at": now.isoformat(), "items": items}


def compose_paper_worker(repository, config, *, fetcher=None, clock=None):
    from jse_adapter import YahooFinanceFetcher
    clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
    fetcher = fetcher or YahooFinanceFetcher()
    loop = PaperLoop(repository, config)
    loop.initialize()
    scheduler = PaperScheduler(repository, config.account_id, interval_seconds=config.interval_seconds)

    def loader():
        charts = {}
        for key in config.universe:
            try:
                chart = fetcher.get_chart(public_share_catalog()[key]["yahoo_symbol"], "1y")
                charts[key] = {name: chart[name] for name in ("symbol", "currency", "interval", "bars")}
                charts[key]["bars"] = charts[key]["bars"][-400:]
            except Exception:
                # Missing data is visible per symbol; exception text can include secrets.
                continue
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
    return {"state": "STALE" if stale else state["status"], "mode": "PAPER", "live_execution": False,
            "account_id": config.account_id, "last_evaluated_at": state["last_evaluated_at"],
            "account": asdict(PaperBroker.restore(state["broker"]).get_account()),
            "positions": state["broker"]["positions"],
            "recent_cycles": repository.paper_records(config.account_id, "cycle", as_of=now.isoformat(), limit=5),
            "recent_outcomes": repository.paper_records(config.account_id, "outcome", as_of=now.isoformat(), limit=5)}
