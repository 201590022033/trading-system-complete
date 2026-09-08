"""Persisted source policy registry for market intelligence.

SourcePolicy from source_catalog.py is the existing contract; this registry
persists it, allows runtime enable/disable, and seeds defaults on first use.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from source_catalog import SourcePolicy, DEFAULT_SOURCE_POLICIES

from .store import MarketIntelligenceStore


SOURCE_CATEGORY_MAP: Dict[str, str] = {
    "market_data": "market_data",
    "authoritative_event": "company_announcements",
    "financial_media": "financial_press",
    "community": "specialist_analysis",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _policy_to_row(policy: SourcePolicy) -> Dict[str, Any]:
    return {
        "source_id": policy.source_id,
        "source_name": policy.source_name,
        "source_class": policy.source_class,
        "authority_tier": policy.authority_tier,
        "access_mode": policy.access_mode,
        "status": policy.status,
        "url": policy.url,
        "enabled": int(policy.enabled),
        "weight": 1.0,
        "minimum_poll_seconds": policy.minimum_poll_seconds,
        "notes": policy.notes,
        "region": None,
        "market_relevance": None,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _row_to_policy(row: Dict[str, Any]) -> SourcePolicy:
    return SourcePolicy(
        source_id=row["source_id"],
        source_name=row["source_name"],
        source_class=row["source_class"],
        authority_tier=row["authority_tier"],
        access_mode=row["access_mode"],
        status=row["status"],
        url=row["url"] or "",
        enabled=bool(row["enabled"]),
        minimum_poll_seconds=row["minimum_poll_seconds"],
        notes=row["notes"] or "",
    )


class SourceRegistry:
    """Persisted registry of market-intelligence source policies."""

    def __init__(self, store: Optional[MarketIntelligenceStore] = None) -> None:
        self.store = store or MarketIntelligenceStore()

    def seed_defaults(self) -> int:
        """Insert default policies if none exist. Returns number inserted."""
        existing = {p["source_id"] for p in self.store.list_source_policies()}
        inserted = 0
        for policy in DEFAULT_SOURCE_POLICIES:
            if policy.source_id in existing:
                continue
            self.store.upsert_source_policy(_policy_to_row(policy))
            inserted += 1
        return inserted

    def list_policies(
        self,
        category: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[SourcePolicy]:
        rows = self.store.list_source_policies()
        policies = [_row_to_policy(r) for r in rows]
        if category:
            policies = [p for p in policies if SOURCE_CATEGORY_MAP.get(p.source_class) == category]
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        return policies

    def get_policy(self, source_id: str) -> Optional[SourcePolicy]:
        row = self.store.get_source_policy(source_id)
        return _row_to_policy(row) if row else None

    def enable(self, source_id: str, enabled: bool) -> SourcePolicy:
        policy = self.get_policy(source_id)
        if policy is None:
            raise KeyError(source_id)
        updated = replace(policy, enabled=enabled)
        self.store.upsert_source_policy(_policy_to_row(updated))
        self.store.audit(
            action="source_enabled" if enabled else "source_disabled",
            entity_type="source_policy",
            entity_id=source_id,
            after={"enabled": enabled},
        )
        return updated

    def update_policy(self, source_id: str, **fields: Any) -> SourcePolicy:
        policy = self.get_policy(source_id)
        if policy is None:
            raise KeyError(source_id)
        before = self.store.get_source_policy(source_id)
        allowed = {"source_name", "notes", "minimum_poll_seconds"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        updated = replace(policy, **updates)
        row = _policy_to_row(updated)
        # Preserve fields that live only in the persisted row, not in SourcePolicy.
        if before:
            for preserved in ("created_at", "weight", "region", "market_relevance"):
                if before.get(preserved) is not None:
                    row[preserved] = before[preserved]
        row["updated_at"] = _now()
        self.store.upsert_source_policy(row)
        self.store.audit(
            action="source_updated",
            entity_type="source_policy",
            entity_id=source_id,
            before=dict(before) if before else None,
            after=row,
        )
        return updated

    def add_policy(self, policy: SourcePolicy) -> SourcePolicy:
        if self.store.get_source_policy(policy.source_id):
            raise ValueError(f"source_id already exists: {policy.source_id}")
        row = _policy_to_row(policy)
        self.store.upsert_source_policy(row)
        self.store.audit(
            action="source_added",
            entity_type="source_policy",
            entity_id=policy.source_id,
            after=row,
        )
        return policy

    def remove_policy(self, source_id: str) -> bool:
        policy = self.store.get_source_policy(source_id)
        if policy is None:
            return False
        # Only allow removal of user-added sources; default catalog sources can be disabled.
        built_in_ids = {p.source_id for p in DEFAULT_SOURCE_POLICIES}
        if source_id in built_in_ids:
            raise ValueError("Cannot remove built-in source; disable it instead")
        deleted = self.store.delete_source_policy(source_id)
        if deleted:
            self.store.audit(
                action="source_removed",
                entity_type="source_policy",
                entity_id=source_id,
            )
        return deleted
