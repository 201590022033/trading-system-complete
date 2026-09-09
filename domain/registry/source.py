"""Canonical source-governance facade over the existing OI4 registry.

Persistence and CRUD remain delegated to ``market_intelligence.SourceRegistry``
and ``MarketIntelligenceStore``. This module adds typed governance metadata but
does not alter collector polling or sentiment behavior.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Optional

from market_intelligence.source_registry import SourceRegistry as LegacySourceRegistry
from source_catalog import DEFAULT_SOURCE_POLICIES, SourcePolicy as LegacySourcePolicy


class GovernanceState(str, Enum):
    MANDATORY = "MANDATORY"
    PRODUCTION = "PRODUCTION"
    SHADOW = "SHADOW"
    RESEARCH = "RESEARCH"
    DISABLED = "DISABLED"
    BLOCKED = "BLOCKED"


def _governance(status: str, enabled: bool) -> GovernanceState:
    if not enabled:
        return GovernanceState.DISABLED
    if status in {"requires_license", "requires_permission", "requires_approved_api", "blocked"}:
        return GovernanceState.BLOCKED
    if status in {"live_existing", "production"}:
        return GovernanceState.PRODUCTION
    return GovernanceState.RESEARCH


@dataclass(frozen=True)
class CanonicalSourcePolicy:
    source_id: str
    display_name: str
    source_type: str
    source_class: str
    endpoint: Optional[str]
    access_mode: str
    enabled: bool
    governance_state: GovernanceState
    authority_tier: int
    manual_weight: float
    learned_weight: Optional[float]
    minimum_poll_seconds: int
    maximum_age_seconds: Optional[int]
    last_successful_fetch: Optional[str]
    failure_count: Optional[int]
    health_state: Optional[str]
    coverage: tuple[str, ...]
    provenance_capable: bool
    data_grade: Optional[str]
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.source_id or not self.display_name or not self.source_class:
            raise ValueError("source identity and class are required")
        if not isinstance(self.governance_state, GovernanceState):
            raise ValueError("explicit source governance state required")
        if self.authority_tier not in {1, 2, 3, 4}:
            raise ValueError("authority tier must be 1 through 4")
        if self.manual_weight < 0 or self.minimum_poll_seconds < 0:
            raise ValueError("manual weight and polling interval cannot be negative")
        if self.maximum_age_seconds is not None and self.maximum_age_seconds < 0:
            raise ValueError("maximum age cannot be negative")
        if self.failure_count is not None and self.failure_count < 0:
            raise ValueError("failure count cannot be negative")
        if not isinstance(self.coverage, tuple):
            raise ValueError("coverage must be immutable")

    @classmethod
    def from_legacy(cls, policy: LegacySourcePolicy, *, manual_weight: float = 1.0,
                    learned_weight: Optional[float] = None, last_successful_fetch: Optional[str] = None,
                    failure_count: Optional[int] = None, health_state: Optional[str] = None) -> "CanonicalSourcePolicy":
        return cls(policy.source_id, policy.source_name, policy.source_class, policy.source_class,
                    policy.url or None, policy.access_mode, policy.enabled,
                    _governance(policy.status, policy.enabled), policy.authority_tier,
                    manual_weight, learned_weight, policy.minimum_poll_seconds, None,
                    last_successful_fetch, failure_count, health_state, (), True, None, policy.notes)

    def to_legacy(self) -> LegacySourcePolicy:
        return LegacySourcePolicy(self.source_id, self.display_name, self.source_class,
                                  self.authority_tier, self.access_mode,
                                  self._legacy_status(), self.endpoint or "", self.enabled,
                                  self.minimum_poll_seconds, self.notes)

    def _legacy_status(self) -> str:
        if self.governance_state is GovernanceState.DISABLED:
            return "disabled"
        if self.governance_state is GovernanceState.BLOCKED:
            return "blocked"
        return "live_existing" if self.governance_state is GovernanceState.PRODUCTION else "research"

    def provenance(self) -> dict[str, str]:
        return {"source_id": self.source_id, "source_class": self.source_class,
                "authority_tier": str(self.authority_tier)}


class CanonicalSourceRegistry:
    """Typed facade; all persistence is delegated to the existing registry."""

    version = "canonical-source-registry-v1"

    def __init__(self, legacy_registry: Optional[LegacySourceRegistry] = None) -> None:
        self.legacy = legacy_registry or LegacySourceRegistry()

    def seed_defaults(self) -> int:
        return self.legacy.seed_defaults()

    def list_policies(self, *, enabled_only: bool = False) -> list[CanonicalSourcePolicy]:
        return [CanonicalSourcePolicy.from_legacy(item) for item in self.legacy.list_policies(enabled_only=enabled_only)]

    def get(self, source_id: str) -> Optional[CanonicalSourcePolicy]:
        item = self.legacy.get_policy(source_id)
        return CanonicalSourcePolicy.from_legacy(item) if item else None

    def register(self, policy: CanonicalSourcePolicy) -> CanonicalSourcePolicy:
        if self.get(policy.source_id) is not None:
            raise ValueError(f"source_id already exists: {policy.source_id}")
        self.legacy.add_policy(policy.to_legacy())
        return policy

    def enable(self, source_id: str, enabled: bool) -> CanonicalSourcePolicy:
        self.legacy.enable(source_id, enabled)
        result = self.get(source_id)
        assert result is not None
        return result

    def update(self, source_id: str, **fields: Any) -> CanonicalSourcePolicy:
        self.legacy.update_policy(source_id, **fields)
        result = self.get(source_id)
        assert result is not None
        return result

    def remove(self, source_id: str) -> bool:
        return self.legacy.remove_policy(source_id)


def default_canonical_policies() -> tuple[CanonicalSourcePolicy, ...]:
    return tuple(CanonicalSourcePolicy.from_legacy(item) for item in DEFAULT_SOURCE_POLICIES)
