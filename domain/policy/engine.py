"""Convert M13 opportunities into non-executable, causal trade-policy plans."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from domain.contracts.policy import CandidateTradePolicy, EntryPolicyType, ExitPolicyType, StopPolicyType
from domain.evaluation.opportunity import ResearchOpportunity
from .families import AUDIT_ONLY, HORIZON_ALIGNED, PolicyFamily, VERSION as FAMILY_VERSION

VERSION = "trade-policy-v1"
NON_EXECUTABLE = "NON_EXECUTABLE_RESEARCH_PLAN"


@dataclass(frozen=True)
class PolicyContext:
    """Causally available scheduling context; no future price is accepted."""

    available_at: datetime
    horizon_end: datetime | None
    decision_bar_seconds: int | None
    current_position_direction: str | None = None
    slippage_assumption: Mapping[str, object] = field(
        default_factory=lambda: {"status": "UNAVAILABLE"})

    def __post_init__(self):
        if self.available_at.tzinfo is None or self.available_at.utcoffset() is None:
            raise ValueError("context availability must be timezone-aware")
        if self.horizon_end is not None and (
                self.horizon_end.tzinfo is None or self.horizon_end.utcoffset() is None):
            raise ValueError("horizon end must be timezone-aware")
        if self.decision_bar_seconds is not None and self.decision_bar_seconds <= 0:
            raise ValueError("decision bar duration must be positive")
        if self.current_position_direction not in {None, "LONG", "SHORT"}:
            raise ValueError("current position direction must be LONG, SHORT or absent")
        object.__setattr__(self, "slippage_assumption",
                           MappingProxyType(dict(self.slippage_assumption)))


@dataclass(frozen=True)
class TradePolicy:
    policy_id: str
    policy_version: str
    policy_family_id: str
    policy_family_version: str
    created_at: datetime
    opportunity_id: str
    opportunity_version: str
    instrument_id: str
    horizon_id: str
    direction: str | None
    status: str
    actionability: str
    entry_type: EntryPolicyType
    entry_reference: str
    entry_timing: str
    allowed_entry_window_start: datetime | None
    allowed_entry_window_end: datetime | None
    entry_price_source: str
    entry_price: float | None
    slippage_assumption: Mapping[str, object]
    invalidation_reason: str
    invalidation_condition: str
    invalidation_time: datetime | None
    stop_type: StopPolicyType
    stop_reference: str
    stop_distance: float | None
    stop_price: float | None
    stop_provenance: Mapping[str, object]
    target_type: str
    target_reference: str
    target_distance: float | None
    target_levels: tuple[float, ...]
    target_provenance: Mapping[str, object]
    trailing_enabled: bool
    trailing_rules: Mapping[str, object]
    ttl_seconds: int | None
    max_holding_seconds: int | None
    time_exit_at: datetime | None
    session_time_stop_rule: str
    exit_rules: tuple[str, ...]
    reversal_required: bool
    reversal_rule: str
    requested_risk_fraction: float | None
    requested_loss_budget: float | None
    requested_gearing: float | None
    risk_approval_status: str
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    opportunity_feature_versions: tuple[str, ...]
    regime_version: str | None
    suitability_version: str
    ranking_version: str
    family_snapshot: CandidateTradePolicy
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        for name in ("created_at", "allowed_entry_window_start", "allowed_entry_window_end",
                     "invalidation_time", "time_exit_at"):
            value = getattr(self, name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if self.direction not in {None, "LONG", "SHORT"}:
            raise ValueError("policy direction must be LONG, SHORT or absent")
        if self.status not in {"READY_FOR_RISK_REVIEW", "WATCH", "UNRESOLVED",
                               "INSUFFICIENT_EVIDENCE", "BLOCKED"}:
            raise ValueError("invalid policy status")
        if self.actionability != NON_EXECUTABLE or self.risk_approval_status != "NOT_EVALUATED":
            raise ValueError("M14 policy must remain non-executable and risk-unapproved")
        for name in ("entry_price", "stop_distance", "stop_price", "target_distance",
                     "requested_risk_fraction", "requested_loss_budget", "requested_gearing"):
            value = getattr(self, name)
            if value is not None and (not isfinite(value) or value < 0):
                raise ValueError(f"{name} must be nonnegative and finite when known")
        if self.requested_risk_fraction is not None and self.requested_risk_fraction > 1:
            raise ValueError("requested risk fraction cannot exceed one")
        if any(not isfinite(value) or value < 0 for value in self.target_levels):
            raise ValueError("target levels must be nonnegative and finite")
        if self.stop_type is StopPolicyType.UNRESOLVED and (
                self.stop_distance is not None or self.stop_price is not None):
            raise ValueError("unresolved stop cannot carry invented geometry")
        if self.entry_price is not None and self.stop_price is not None:
            if ((self.direction == "LONG" and self.stop_price >= self.entry_price) or
                    (self.direction == "SHORT" and self.stop_price <= self.entry_price)):
                raise ValueError("stop price must be on the loss side of entry")
        if self.target_type == "NONE" and (self.target_distance is not None or self.target_levels):
            raise ValueError("absent target cannot carry target geometry")
        if self.trailing_enabled and not self.trailing_rules:
            raise ValueError("enabled trailing requires explicit rules")
        if self.status == "READY_FOR_RISK_REVIEW" and (
                self.direction is None or self.entry_type is EntryPolicyType.UNRESOLVED or
                self.stop_type is StopPolicyType.UNRESOLVED or
                (self.stop_distance is None and self.stop_price is None)):
            raise ValueError("risk review requires resolved direction, entry and stop")
        for name in ("ttl_seconds", "max_holding_seconds"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when known")
        if self.time_exit_at is not None and self.time_exit_at <= self.created_at:
            raise ValueError("time exit must follow policy creation")
        if self.allowed_entry_window_start is not None and self.allowed_entry_window_end is not None:
            if self.allowed_entry_window_end <= self.allowed_entry_window_start:
                raise ValueError("entry window must end after it starts")
            if self.time_exit_at is not None and self.allowed_entry_window_end > self.time_exit_at:
                raise ValueError("entry window cannot extend beyond time exit")
        for name in ("slippage_assumption", "stop_provenance", "target_provenance",
                     "trailing_rules", "provenance"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self):
        result = dict(self.__dict__)
        for name in ("created_at", "allowed_entry_window_start", "allowed_entry_window_end",
                     "invalidation_time", "time_exit_at"):
            result[name] = getattr(self, name).isoformat() if getattr(self, name) else None
        for name in ("entry_type", "stop_type"):
            result[name] = getattr(self, name).value
        for name in ("slippage_assumption", "stop_provenance", "target_provenance",
                     "trailing_rules", "provenance"):
            result[name] = dict(getattr(self, name))
        result["family_snapshot"] = self.family_snapshot.to_dict()
        return result


def _canonical_horizon(horizon_id):
    if horizon_id.startswith("intraday_") and horizon_id.endswith("m"):
        try:
            return int(horizon_id.removeprefix("intraday_").removesuffix("m")) > 0
        except ValueError:
            return False
    return horizon_id.startswith("daily_")


class TradePolicyEngine:
    """Build planning records only; it has no risk or execution dependency."""

    def _audit_policy(self, opportunity, created_at, status, blockers):
        family = AUDIT_ONLY
        snapshot = CandidateTradePolicy(
            family.family_id, family.family_version, family.entry_type,
            family.stop_type, family.primary_exit_type, {"actionability": NON_EXECUTABLE})
        return self._build(
            opportunity, created_at, family, snapshot, status=status, direction=None,
            entry_reference="UNRESOLVED", entry_timing="NO_ENTRY_INTENT",
            entry_start=None, entry_end=None, time_exit=None, holding=None,
            reversal_required=False, reversal_rule="NO_POSITION_TRANSITION",
            reasons=("M13_OPPORTUNITY_NOT_ACTIONABLE",), blockers=blockers,
            slippage={"status": "UNAVAILABLE"})

    def create(self, opportunity, *, created_at, context):
        if not isinstance(opportunity, ResearchOpportunity):
            raise TypeError("canonical M13 ResearchOpportunity required")
        if not isinstance(context, PolicyContext):
            raise TypeError("canonical PolicyContext required")
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        created_at = created_at.astimezone(timezone.utc)
        blockers = list(opportunity.blockers)
        if opportunity.evaluated_at > created_at:
            blockers.append("FUTURE_OPPORTUNITY")
        if context.available_at > created_at:
            blockers.append("FUTURE_POLICY_CONTEXT")
        if opportunity.eligibility_status in {"BLOCKED", "UNSUPPORTED"} or blockers:
            return self._audit_policy(opportunity, created_at, "BLOCKED", tuple(dict.fromkeys(blockers)))
        if opportunity.eligibility_status == "INSUFFICIENT_EVIDENCE":
            return self._audit_policy(opportunity, created_at, "INSUFFICIENT_EVIDENCE",
                                      ("REQUIRED_OPPORTUNITY_EVIDENCE_ABSENT",))
        if opportunity.eligibility_status == "WATCH" or opportunity.direction in {"WATCH", "UNKNOWN"}:
            return self._audit_policy(opportunity, created_at, "WATCH", ("NO_ACTIONABLE_DIRECTION",))
        if opportunity.direction not in {"LONG", "SHORT"}:
            return self._audit_policy(opportunity, created_at, "UNRESOLVED", ("DIRECTION_UNRESOLVED",))

        family = HORIZON_ALIGNED
        unresolved = []
        if not _canonical_horizon(opportunity.horizon_id):
            unresolved.append("NONCANONICAL_HORIZON_ID")
        if context.horizon_end is None or context.horizon_end <= created_at:
            unresolved.append("HORIZON_END_UNAVAILABLE")
        if context.decision_bar_seconds is None:
            unresolved.append("DECISION_BAR_DURATION_UNAVAILABLE")
        holding = (int((context.horizon_end - created_at).total_seconds())
                   if context.horizon_end is not None and context.horizon_end > created_at else None)
        entry_end = (min(created_at + timedelta(seconds=context.decision_bar_seconds), context.horizon_end)
                     if not unresolved else None)
        if entry_end is not None and entry_end <= created_at:
            unresolved.append("ENTRY_WINDOW_UNAVAILABLE")
            entry_end = None
        reversal = (context.current_position_direction is not None and
                    context.current_position_direction != opportunity.direction)
        snapshot = CandidateTradePolicy(
            family.family_id, family.family_version, family.entry_type, family.stop_type,
            family.primary_exit_type,
            {"entry_reference": "NEXT_OBSERVED_CANONICAL_BAR_OPEN",
             "horizon_id": opportunity.horizon_id, "actionability": NON_EXECUTABLE,
             "stop_status": "UNRESOLVED", "target_status": "NONE"})
        reasons = ["NEXT_OBSERVED_BAR_OPEN_PRESERVES_HR11_CAUSAL_CONVENTION",
                   "HORIZON_ALIGNED_TIME_EXIT", "STOP_EVIDENCE_UNAVAILABLE",
                   "TARGET_NOT_REQUIRED_BY_SUPPORTED_FAMILY", "TRAILING_NOT_SUPPORTED"]
        if reversal:
            reasons.append("OPPOSING_POSITION_REQUIRES_EXIT_BEFORE_NEW_POLICY_REVIEW")
        # No existing causal stop-distance implementation is validated. A directional
        # plan therefore remains unresolved rather than inventing executable geometry.
        unresolved.append("STOP_POLICY_UNRESOLVED")
        return self._build(
            opportunity, created_at, family, snapshot, status="UNRESOLVED",
            direction=opportunity.direction, entry_reference="NEXT_OBSERVED_CANONICAL_BAR_OPEN",
            entry_timing="AFTER_POLICY_CREATION_WHEN_NEXT_BAR_OPEN_IS_OBSERVED",
            entry_start=created_at if entry_end else None, entry_end=entry_end,
            time_exit=context.horizon_end if holding is not None else None, holding=holding,
            reversal_required=reversal,
            reversal_rule=("EXIT_EXISTING_POSITION_THEN_REQUIRE_SEPARATE_NEW_POLICY_REVIEW"
                           if reversal else "EXIT_ON_VALID_OPPOSING_SIGNAL; NEVER_AUTO_FLIP"),
            reasons=tuple(reasons), blockers=tuple(dict.fromkeys(unresolved)),
            slippage=context.slippage_assumption)

    def _build(self, opportunity, created_at, family: PolicyFamily, snapshot, *, status,
               direction, entry_reference, entry_timing, entry_start, entry_end,
               time_exit, holding, reversal_required, reversal_rule, reasons, blockers, slippage):
        identity = f"{opportunity.opportunity_id}|{created_at.isoformat()}|{family.family_id}|{VERSION}"
        policy_id = "policy:" + sha256(identity.encode()).hexdigest()
        return TradePolicy(
            policy_id, VERSION, family.family_id, family.family_version, created_at,
            opportunity.opportunity_id, opportunity.opportunity_version,
            opportunity.instrument_id, opportunity.horizon_id, direction, status,
            NON_EXECUTABLE, family.entry_type, entry_reference, entry_timing,
            entry_start, entry_end, "OBSERVED_CANONICAL_BAR_OPEN; PRICE_UNAVAILABLE_UNTIL_OBSERVED",
            None, slippage,
            "THESIS_INVALID_BEFORE_ENTRY_OR_EXIT_REVIEW_REQUIRED",
            "OPPORTUNITY_BECOMES_INELIGIBLE_OR_VALID_OPPOSING_DIRECTION_APPEARS",
            None, family.stop_type, "UNRESOLVED_NO_VALIDATED_CAUSAL_STOP_INPUT",
            None, None, {"status": "UNRESOLVED", "reason": "NO_VALIDATED_STOP_IMPLEMENTATION"},
            "NONE", "NO_TARGET_IN_SUPPORTED_HORIZON_TIME_EXIT_FAMILY", None, (),
            {"status": "NONE"}, False, {"status": "UNSUPPORTED"},
            holding, holding, time_exit,
            "EXIT_AT_CANONICAL_HORIZON_END; SESSION_BOUNDARY_SUPPLIED_UPSTREAM",
            ("STOP_EXIT_IF_LATER_RISK_REVIEW_DEFINES_STOP", "TIME_EXIT_AT_HORIZON_END",
             "SIGNAL_REVERSAL_REQUIRES_EXIT_REVIEW", "INVALIDATION_EXIT_BEFORE_ENTRY"),
            reversal_required, reversal_rule, None, None, None, "NOT_EVALUATED",
            tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(blockers)),
            opportunity.input_feature_versions, opportunity.regime_version,
            opportunity.suitability_version, opportunity.ranking_version, snapshot,
            {"opportunity_id": opportunity.opportunity_id,
             "opportunity_version": opportunity.opportunity_version,
             "ranking_version": opportunity.ranking_version,
             "policy_family_version": FAMILY_VERSION},
        )


def create_trade_policy(opportunity, *, created_at, context):
    return TradePolicyEngine().create(opportunity, created_at=created_at, context=context)


__all__ = ["NON_EXECUTABLE", "PolicyContext", "TradePolicy", "TradePolicyEngine",
           "VERSION", "create_trade_policy"]
