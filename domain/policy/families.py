"""Versioned policy families supported by existing causal research semantics."""

from dataclasses import dataclass

from domain.contracts.policy import EntryPolicyType, ExitPolicyType, StopPolicyType

VERSION = "trade-policy-families-v1"


@dataclass(frozen=True)
class PolicyFamily:
    family_id: str
    family_version: str
    entry_type: EntryPolicyType
    stop_type: StopPolicyType
    primary_exit_type: ExitPolicyType
    trailing_supported: bool
    evidence_basis: str


HORIZON_ALIGNED = PolicyFamily(
    "horizon-aligned-next-bar-time-exit", VERSION,
    EntryPolicyType.CONFIRMATION_ENTRY, StopPolicyType.UNRESOLVED,
    ExitPolicyType.TIME_EXPIRY, False,
    "HR11 causal next-observed-bar-open paper convention and canonical M8 horizon end",
)

AUDIT_ONLY = PolicyFamily(
    "non-actionable-audit-only", VERSION,
    EntryPolicyType.UNRESOLVED, StopPolicyType.UNRESOLVED,
    ExitPolicyType.UNRESOLVED, False,
    "M13 non-actionable opportunity state",
)

__all__ = ["AUDIT_ONLY", "HORIZON_ALIGNED", "PolicyFamily", "VERSION"]
