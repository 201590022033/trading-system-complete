"""Exact, nullable provenance. Absence means legacy, never an inferred strategy."""
from dataclasses import dataclass
from hashlib import sha256
import json
from collections.abc import Mapping
from functools import wraps
from .profile import StrategyProfileRef


def reference(value):
    if value is None:
        return None
    if isinstance(value, StrategyProfileRef):
        return value
    if isinstance(value, Mapping):
        identity, version = value.get("strategy_profile_id"), value.get("strategy_profile_version")
    else:
        identity = getattr(value, "strategy_profile_id", None)
        version = getattr(value, "strategy_profile_version", None)
    if identity is None and version is None:
        return None
    return StrategyProfileRef(identity, version)


def fields(value):
    ref = reference(value)
    return ref.to_dict() if ref else {}


def same_strategy(*values):
    refs = tuple(reference(value) for value in values)
    if any(ref != refs[0] for ref in refs[1:]):
        raise ValueError("strategy profile identity/version mismatch")


def identity_suffix(value):
    ref = reference(value)
    return f"|{ref.strategy_profile_id}|{ref.strategy_profile_version}" if ref else ""


def attributed_dto(serializer):
    @wraps(serializer)
    def serialize(value, *args, **kwargs):
        return {**serializer(value, *args, **kwargs), **fields(value),
                "strategy_attribution_state": "ATTRIBUTED" if reference(value) else "LEGACY_UNATTRIBUTED"}
    return serialize


@dataclass(frozen=True, kw_only=True)
class StrategyAttributed:
    strategy_profile_id: str | None = None
    strategy_profile_version: str | None = None

    def __post_init__(self):
        reference(self)


def freeze_profile(profile):
    snapshot = profile.to_dict()
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {**profile.reference.to_dict(), "strategy_profile_snapshot": snapshot,
            "strategy_profile_sha256": sha256(raw.encode()).hexdigest(),
            "strategy_attribution_schema": "strategy-attribution-v1"}


def validate_frozen_profile(payload, *, definition=None):
    ref = reference(payload)
    if ref is None:
        if any(key in payload for key in ("strategy_profile_snapshot", "strategy_profile_sha256")):
            raise ValueError("profile snapshot without exact reference")
        return None
    snapshot = payload.get("strategy_profile_snapshot", definition)
    if not isinstance(snapshot, dict):
        raise ValueError("attributed job requires frozen profile definition")
    same_strategy(ref, snapshot)
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if payload.get("strategy_profile_sha256") != sha256(raw.encode()).hexdigest():
        raise ValueError("frozen strategy definition checksum mismatch")
    if payload.get("strategy_attribution_schema") != "strategy-attribution-v1":
        raise ValueError("unsupported strategy attribution schema")
    return ref
