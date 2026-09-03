"""Point-in-time historical feature records for research/shadow use only."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


STORE_VERSION = "historical-feature-store-v1"
FEATURE_GROUPS = {
    "raw_market", "technical", "regime", "macro", "cross_asset",
    "commodity", "fx", "source_event",
}
REVISION_STATES = {"not_applicable", "initial", "revised", "final"}


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class FeatureProvenance:
    source_id: str
    source_name: str
    source_uri: str = ""
    licence: str = "unknown"
    retrieval_id: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.source_name.strip():
            raise ValueError("provenance requires source_id and source_name")


@dataclass(frozen=True)
class HistoricalFeature:
    instrument: str
    asset_class: str
    sector: str
    profile: str
    feature_group: str
    feature_name: str
    value: Any
    event_time: datetime
    available_time: datetime
    decision_time: datetime
    provenance: FeatureProvenance
    is_raw: bool
    feature_version: str = "v1"
    revision_status: str = "not_applicable"
    supersedes_id: str = ""
    capability_available: bool = True
    unavailable_reason: str = ""
    input_record_ids: tuple[str, ...] = field(default_factory=tuple)
    store_version: str = STORE_VERSION

    def __post_init__(self) -> None:
        if not self.instrument.strip() or not self.feature_name.strip():
            raise ValueError("instrument and feature_name are required")
        if self.feature_group not in FEATURE_GROUPS:
            raise ValueError(f"unsupported feature_group: {self.feature_group}")
        if self.revision_status not in REVISION_STATES:
            raise ValueError(f"unsupported revision_status: {self.revision_status}")
        event = _utc(self.event_time, "event_time")
        available = _utc(self.available_time, "available_time")
        decision = _utc(self.decision_time, "decision_time")
        object.__setattr__(self, "event_time", event)
        object.__setattr__(self, "available_time", available)
        object.__setattr__(self, "decision_time", decision)
        if available > decision:
            raise ValueError("available_time must be <= decision_time")
        if self.is_raw and self.input_record_ids:
            raise ValueError("raw features cannot declare derived-input lineage")
        if not self.is_raw and self.capability_available and not self.input_record_ids:
            raise ValueError("available derived features require input_record_ids")
        if self.capability_available and self.value is None:
            raise ValueError("available features require a value")
        if not self.capability_available:
            if not self.unavailable_reason.strip():
                raise ValueError("unavailable features require unavailable_reason")
            if self.value is not None:
                raise ValueError("unavailable feature value must be None")

    @property
    def record_id(self) -> str:
        identity = "|".join((
            self.instrument, self.feature_group, self.feature_name,
            self.event_time.isoformat(), self.available_time.isoformat(),
            self.feature_version, self.revision_status, self.provenance.source_id,
            self.provenance.retrieval_id,
        ))
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("event_time", "available_time", "decision_time"):
            result[key] = getattr(self, key).isoformat()
        result["input_record_ids"] = list(self.input_record_ids)
        result["record_id"] = self.record_id
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "HistoricalFeature":
        data = dict(value)
        expected_id = data.pop("record_id", "")
        for key in ("event_time", "available_time", "decision_time"):
            data[key] = datetime.fromisoformat(data[key])
        data["provenance"] = FeatureProvenance(**data["provenance"])
        data["input_record_ids"] = tuple(data.get("input_record_ids", ()))
        record = cls(**data)
        if expected_id and expected_id != record.record_id:
            raise ValueError("record_id does not match record content")
        return record


class PointInTimeFeatureStore:
    """Append-only JSONL store with revision-aware point-in-time selection."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def append(self, records: Iterable[HistoricalFeature]) -> int:
        items = list(records)
        if not items:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing_ids = {record.record_id for record in self.read_all()}
        duplicate = existing_ids.intersection(record.record_id for record in items)
        if duplicate or len({record.record_id for record in items}) != len(items):
            raise ValueError("duplicate feature record_id")
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            for record in items:
                handle.write(json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
        return len(items)

    def read_all(self) -> list[HistoricalFeature]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as handle:
            return [HistoricalFeature.from_dict(json.loads(line)) for line in handle if line.strip()]

    def as_of(
        self,
        decision_time: datetime,
        *,
        instrument: Optional[str] = None,
        feature_names: Optional[set[str]] = None,
    ) -> list[HistoricalFeature]:
        cutoff = _utc(decision_time, "decision_time")
        eligible = [
            record for record in self.read_all()
            if record.available_time <= cutoff
            and record.decision_time <= cutoff
            and (instrument is None or record.instrument == instrument)
            and (feature_names is None or record.feature_name in feature_names)
        ]
        latest: dict[tuple[str, str, str, datetime], HistoricalFeature] = {}
        for record in eligible:
            key = (record.instrument, record.feature_group, record.feature_name, record.event_time)
            if key not in latest or record.available_time > latest[key].available_time:
                latest[key] = record
        return sorted(latest.values(), key=lambda item: (
            item.instrument, item.feature_group, item.feature_name, item.event_time
        ))


def write_schema(path: Path | str) -> None:
    schema = {
        "store_version": STORE_VERSION,
        "format": "append-only JSON Lines; optional Parquet projection when an engine is installed",
        "required_times": ["event_time", "available_time", "decision_time"],
        "eligibility_rule": "available_time <= decision_time",
        "feature_groups": sorted(FEATURE_GROUPS),
        "revision_states": sorted(REVISION_STATES),
        "raw_derived_rule": "is_raw=false requires input_record_ids when available",
        "required_identity": ["instrument", "asset_class", "sector", "profile", "feature_name", "feature_version"],
        "capability_fields": ["capability_available", "unavailable_reason"],
        "provenance_fields": list(FeatureProvenance.__dataclass_fields__),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
