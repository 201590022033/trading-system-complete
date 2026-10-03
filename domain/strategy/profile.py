"""Immutable strategy declarations; discovery is never execution authorization."""
from dataclasses import dataclass
from enum import Enum
import re


class StrategyLifecycle(str, Enum):
    ACTIVE_RESEARCH_PAPER = "ACTIVE_RESEARCH_PAPER"
    DEVELOPMENT_DATA_VALIDATION_REQUIRED = "DEVELOPMENT_DATA_VALIDATION_REQUIRED"
    DEVELOPMENT = "DEVELOPMENT"
    DEPRECATED = "DEPRECATED"


class CapabilityState(str, Enum):
    IMPLEMENTED_REUSABLE = "IMPLEMENTED_REUSABLE"
    BLOCKED = "BLOCKED"
    PLANNED = "PLANNED"


@dataclass(frozen=True)
class StrategyProfileRef:
    strategy_profile_id: str
    strategy_profile_version: str

    def __post_init__(self):
        if not isinstance(self.strategy_profile_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", self.strategy_profile_id):
            raise ValueError("stable strategy profile ID required")
        if not isinstance(self.strategy_profile_version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", self.strategy_profile_version):
            raise ValueError("explicit semantic strategy profile version required")

    def to_dict(self):
        return {"strategy_profile_id": self.strategy_profile_id,
                "strategy_profile_version": self.strategy_profile_version}


@dataclass(frozen=True)
class StrategyCapability:
    capability_id: str
    state: CapabilityState
    description: str
    component_references: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.capability_id, str) or not self.capability_id or not isinstance(self.description, str) or not self.description or not isinstance(self.state, CapabilityState):
            raise ValueError("capability identity, state and explanation required")
        object.__setattr__(self, "component_references", tuple(self.component_references))
        if any(not isinstance(value, str) or not value for value in self.component_references):
            raise ValueError("component references must be immutable nonempty strings")
        if self.state is CapabilityState.IMPLEMENTED_REUSABLE and not self.component_references:
            raise ValueError("implemented capability requires existing component references")

    def to_dict(self):
        return {"capability_id": self.capability_id, "state": self.state.value,
                "description": self.description, "component_references": list(self.component_references)}


@dataclass(frozen=True)
class StrategyProfile:
    reference: StrategyProfileRef
    display_name: str
    card_title: str
    holding_period_label: str
    lifecycle: StrategyLifecycle
    strategy_family: str
    universe_scope: tuple[str, ...]
    decision_timeframe: str
    intended_horizon_ids: tuple[str, ...]
    allowed_research_modes: tuple[str, ...]
    capabilities: tuple[StrategyCapability, ...]
    limitations: tuple[str, ...]
    canonical_workflow_tab: str | None = None

    def __post_init__(self):
        if not isinstance(self.reference, StrategyProfileRef) or not isinstance(self.lifecycle, StrategyLifecycle):
            raise ValueError("typed strategy reference and lifecycle required")
        if not all(isinstance(value, str) and value for value in
                   (self.display_name, self.card_title, self.holding_period_label, self.strategy_family, self.decision_timeframe)):
            raise ValueError("strategy scope, intent and limitations must be explicit")
        for name in ("universe_scope", "intended_horizon_ids", "allowed_research_modes", "capabilities", "limitations"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for name in ("universe_scope", "intended_horizon_ids", "limitations"):
            values = getattr(self, name)
            if not values or any(not isinstance(value, str) or not value for value in values):
                raise ValueError("explicit immutable string scope/intent/limitations required")
        if not self.allowed_research_modes or not set(self.allowed_research_modes) <= {"RESEARCH", "SHADOW", "PAPER"}:
            raise ValueError("only research, shadow and paper intent permitted")
        if any(not isinstance(item, StrategyCapability) for item in self.capabilities):
            raise ValueError("typed capability declarations required")
        if len({item.capability_id for item in self.capabilities}) != len(self.capabilities):
            raise ValueError("duplicate strategy capability")
        if self.canonical_workflow_tab not in {None, "canonical-opportunities"}:
            raise ValueError("only the existing canonical research workspace may be linked")
        if self.canonical_workflow_tab and self.lifecycle is not StrategyLifecycle.ACTIVE_RESEARCH_PAPER:
            raise ValueError("development placeholders cannot advertise a runtime workflow")

    def to_dict(self):
        label = {StrategyLifecycle.ACTIVE_RESEARCH_PAPER: "ACTIVE RESEARCH / PAPER",
                 StrategyLifecycle.DEVELOPMENT_DATA_VALIDATION_REQUIRED: "DEVELOPMENT / DATA VALIDATION REQUIRED",
                 StrategyLifecycle.DEVELOPMENT: "DEVELOPMENT", StrategyLifecycle.DEPRECATED: "DEPRECATED"}[self.lifecycle]
        return {**self.reference.to_dict(), "display_name": self.display_name, "card_title": self.card_title,
                "lifecycle_label": label,
                "holding_period_label": self.holding_period_label, "lifecycle": self.lifecycle.value,
                "strategy_family": self.strategy_family, "universe_scope": list(self.universe_scope),
                "decision_timeframe": self.decision_timeframe, "intended_horizon_ids": list(self.intended_horizon_ids),
                "horizon_semantics": "DECLARED_INTENT_NOT_RUNTIME_CONFIGURATION",
                "allowed_research_modes": list(self.allowed_research_modes),
                "capabilities": [item.to_dict() for item in self.capabilities],
                "limitations": list(self.limitations), "canonical_workflow_tab": self.canonical_workflow_tab,
                "attribution_state": ("EXACT_VERSION_NEW_RUNS_ONLY_LEGACY_UNATTRIBUTED"
                    if any(item.capability_id == "profile_attribution" and item.state is CapabilityState.IMPLEMENTED_REUSABLE
                           for item in self.capabilities) else "FOUNDATION_ONLY_NOT_PROPAGATED_TO_EXISTING_RECORDS"),
                "validated_strategy": False, "strategy_execution_enabled": False, "live_execution": False}
