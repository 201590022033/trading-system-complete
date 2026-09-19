"""Causal input adapters; news analyses remain labelled opinions."""
from collections.abc import Mapping
from math import isfinite
from shadow_learning import timestamp, _freeze


def causal_bundle(bundle, cutoff):
    def valid(value):
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"evaluated_at", "available_at", "updated_at", "observed_at",
                           "published_at", "last_available_at", "matured_through"} and child:
                    try:
                        if timestamp(child) > cutoff:
                            return False
                    except (TypeError, ValueError):
                        return False
                if not valid(child):
                    return False
        elif isinstance(value, (list, tuple)):
            return all(valid(child) for child in value)
        elif isinstance(value, float) and not isfinite(value):
            return False
        return True
    return _freeze({key: value for key, value in bundle.items() if valid(value)})


def news_context(report, key, cutoff):
    """Only a timestamped completed snapshot can contribute context."""
    unavailable = {"state": "UNAVAILABLE", "reason": "CAUSAL_NEWS_SNAPSHOT_UNAVAILABLE"}
    if not report:
        return unavailable
    try:
        available = timestamp(report["available_at"])
        if available > cutoff or (cutoff - available).total_seconds() > 86400:
            return unavailable
        items = []
        for item in report.get("items", ())[:100]:
            published = timestamp(item["timestamp"])
            if published > available or not item.get("source"):
                continue
            if not any(a.get("name") == key for a in item.get("assets", ())):
                continue
            score = float(item["score"])
            if not isfinite(score) or not -1 <= score <= 1:
                continue
            items.append({"source": item["source"], "url": item.get("url"),
                          "published_at": published.isoformat(),
                          "available_at": available.isoformat(), "score": score,
                          "analysis_kind": "OPINION_NOT_VERIFIED_FACT",
                          "method": "LLM" if item.get("llm_used") else "KEYWORD"})
        return {"state": "AVAILABLE" if items else "UNAVAILABLE",
                "available_at": available.isoformat(), "items": items,
                "macro": "UNAVAILABLE_NO_VALIDATED_ASSET_MAPPING"}
    except (KeyError, TypeError, ValueError):
        return unavailable
