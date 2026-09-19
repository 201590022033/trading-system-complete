"""Persist existing collector output without fabricating publication or analysis clocks."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from evidence import EvidenceRecord
from shadow_learning import stable_id, timestamp
from .public_research import public_share_catalog


def persist_news_report(repository, report, *, observed_at=None):
    now = timestamp(observed_at) if observed_at else datetime.now(timezone.utc)
    from market_intelligence.source_registry import SourceRegistry
    SourceRegistry(repository.store).seed_defaults()
    count = 0
    for item in report.get("items", ())[:100]:
        source = item.get("source", "")
        source_id = "moneyweb_sens" if "sens" in source.lower() else "moneyweb_rss" if "moneyweb" in source.lower() else None
        policy = repository.get_source_policy(source_id) if source_id else None
        if not policy or not policy.enabled or policy.governance_state.value in {"BLOCKED", "DISABLED"}:
            continue
        try:
            published = timestamp(item["timestamp"])
            score = float(item["score"])
            if published > now or not isfinite(score) or not -1 <= score <= 1:
                continue
            if not item.get("headline"):
                continue
        except (KeyError, TypeError, ValueError):
            continue
        article = stable_id("article", source_id, item.get("url"), item["headline"], published.isoformat())
        analysis = {key: item.get(key) for key in ("score", "summary", "assets", "llm_used", "analysis_provider", "analysis_model")}
        digest = sha256(json.dumps(analysis, sort_keys=True, allow_nan=False).encode()).hexdigest()
        eid = stable_id("news-analysis", article, digest)
        assets = [x["name"] for x in item.get("assets", ()) if isinstance(x, dict) and x.get("name")]
        tickers = [x for x in assets if x in public_share_catalog()]
        record = EvidenceRecord(eid, source_id, source, policy.source_class, policy.authority_tier,
            item["headline"], item.get("summary") or item["headline"], item.get("url"), now.isoformat(),
            published.isoformat(), now.isoformat(), tickers=tickers,
            assets=[x for x in assets if x not in tickers], sentiment=item.get("sentiment", "neutral"),
            score=score, parser_version="persisted-public-analysis-v1",
            metadata={"article_id": article, "llm_used": bool(item.get("llm_used")),
                      "analysis_provider": item.get("analysis_provider", "keywords"),
                      "analysis_model": item.get("analysis_model"), "analysis_kind": "OPINION_NOT_VERIFIED_FACT"})
        with repository.transaction():
            if repository.backend == "postgresql":
                lock = int.from_bytes(sha256(eid.encode()).digest()[:8], "big", signed=True)
                repository._job_sql("SELECT pg_advisory_xact_lock(?)", (lock,), rows=True)
            if repository.get_evidence(eid) is None:
                repository.save_evidence(record)
                count += 1
    return count
