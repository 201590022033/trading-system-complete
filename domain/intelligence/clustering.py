"""Deterministic, provenance-preserving event clustering.

This is a Tier-2 research layer. Exact ``EvidenceRecord`` identity
deduplication remains the Tier-1 behavior in :mod:`evidence`; records are never
deleted or rewritten here.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import Iterable, Optional

from evidence import EvidenceRecord, deduplicate_evidence


@dataclass(frozen=True)
class EventClusterPolicy:
    policy_id: str
    policy_version: str
    event_window_seconds: int
    text_similarity_method: str
    text_similarity_threshold: float
    required_entity_overlap: bool
    normalization_rules: tuple[str, ...] = ("lowercase", "alphanumeric_tokens", "stopword_filter")
    language: str = "en"
    configuration_state: str = "RESEARCH"

    def __post_init__(self) -> None:
        if not self.policy_id or not self.policy_version:
            raise ValueError("cluster policy identity and version are required")
        if self.event_window_seconds <= 0:
            raise ValueError("event window must be positive")
        if self.text_similarity_method != "token_jaccard":
            raise ValueError("only deterministic token_jaccard is supported in M5")
        if not 0.0 <= self.text_similarity_threshold <= 1.0:
            raise ValueError("similarity threshold must be between zero and one")
        if not isinstance(self.normalization_rules, tuple) or not self.language:
            raise ValueError("normalization rules and language are required")


@dataclass(frozen=True)
class ClusteredEvent:
    event_id: str
    cluster_policy_id: str
    cluster_policy_version: str
    first_observed_at: str
    latest_observed_at: str
    primary_headline: str
    underlying_evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    entity_references: tuple[str, ...]
    macro_references: tuple[str, ...]
    consensus_direction: int
    aggregate_strength: float
    duplicate_evidence_count: int

    def __post_init__(self) -> None:
        if not self.event_id or not self.underlying_evidence_ids:
            raise ValueError("cluster identity and members are required")
        if self.consensus_direction not in {-1, 0, 1}:
            raise ValueError("consensus direction must be -1, 0 or 1")
        if not 0.0 <= self.aggregate_strength <= 1.0:
            raise ValueError("aggregate strength must be between zero and one")
        if self.duplicate_evidence_count != max(0, len(self.underlying_evidence_ids) - 1):
            raise ValueError("duplicate count must match cluster membership")

    def to_dict(self) -> dict:
        return {"event_id": self.event_id, "cluster_policy_id": self.cluster_policy_id,
                "cluster_policy_version": self.cluster_policy_version,
                "first_observed_at": self.first_observed_at, "latest_observed_at": self.latest_observed_at,
                "primary_headline": self.primary_headline,
                "underlying_evidence_ids": list(self.underlying_evidence_ids),
                "source_ids": list(self.source_ids), "entity_references": list(self.entity_references),
                "macro_references": list(self.macro_references),
                "consensus_direction": self.consensus_direction,
                "aggregate_strength": self.aggregate_strength,
                "duplicate_evidence_count": self.duplicate_evidence_count}


STOPWORDS = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the", "to", "with"}


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("evidence timestamps must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def normalized_tokens(headline: str) -> frozenset[str]:
    tokens = re.findall(r"[a-z0-9]+", (headline or "").lower())
    return frozenset(token for token in tokens if token not in STOPWORDS)


def token_jaccard(left: str, right: str) -> float:
    a, b = normalized_tokens(left), normalized_tokens(right)
    if not a or not b:
        return 1.0 if a == b and bool(a) else 0.0
    return len(a & b) / len(a | b)


def _references(record: EvidenceRecord) -> frozenset[str]:
    return frozenset(item.upper() for item in (*record.tickers, *record.assets, *record.sectors) if item)


def _direction(record: EvidenceRecord) -> int:
    return 1 if record.sentiment == "bullish" else -1 if record.sentiment == "bearish" else 0


class EventClusterer:
    def __init__(self, policy: EventClusterPolicy) -> None:
        self.policy = policy

    def _matches(self, record: EvidenceRecord, member: EvidenceRecord) -> bool:
        left_refs, right_refs = _references(record), _references(member)
        if self.policy.required_entity_overlap and left_refs and right_refs and not left_refs.intersection(right_refs):
            return False
        left_time = _timestamp(record.published_at or record.observed_at)
        right_time = _timestamp(member.published_at or member.observed_at)
        if abs((left_time - right_time).total_seconds()) > self.policy.event_window_seconds:
            return False
        return token_jaccard(record.headline, member.headline) >= self.policy.text_similarity_threshold

    def cluster(self, records: Iterable[EvidenceRecord], *, as_of: Optional[datetime] = None) -> tuple[ClusteredEvent, ...]:
        if as_of is not None and (as_of.tzinfo is None or as_of.utcoffset() is None):
            raise ValueError("as_of must be timezone-aware")
        cutoff = as_of.astimezone(timezone.utc) if as_of else None
        unique = deduplicate_evidence(records)
        eligible = [record for record in unique if cutoff is None or _timestamp(record.ingested_at) <= cutoff]
        eligible.sort(key=lambda item: (_timestamp(item.published_at or item.observed_at), item.evidence_id))
        groups: list[list[EvidenceRecord]] = []
        for record in eligible:
            group = next((candidate for candidate in groups if any(self._matches(record, member) for member in candidate)), None)
            if group is None:
                groups.append([record])
            else:
                group.append(record)
        return tuple(self._event(group) for group in groups)

    def _event(self, members: list[EvidenceRecord]) -> ClusteredEvent:
        ordered = sorted(members, key=lambda item: (_timestamp(item.published_at or item.observed_at), item.evidence_id))
        member_ids = tuple(item.evidence_id for item in ordered)
        identity = "|".join((self.policy.policy_id, self.policy.policy_version, *member_ids))
        directions = [_direction(item) for item in ordered]
        total = sum(directions)
        strength = sum(min(1.0, abs(float(item.score))) for item in ordered) / len(ordered)
        return ClusteredEvent(
            hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24], self.policy.policy_id,
            self.policy.policy_version, ordered[0].observed_at, ordered[-1].observed_at,
            ordered[0].headline, member_ids,
            tuple(sorted({item.source_id for item in ordered})),
            tuple(sorted(set().union(*(set(item.tickers) | set(item.sectors) for item in ordered)))),
            tuple(sorted(set().union(*(set(item.assets) for item in ordered)))),
            1 if total > 0 else -1 if total < 0 else 0, round(strength, 12), len(ordered) - 1)
