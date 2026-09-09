"""Versioned feature definitions and an execution-isolated registry."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence


class FeatureStatus(str, Enum):
    LEGACY = "LEGACY"
    CANDIDATE = "CANDIDATE"


@dataclass(frozen=True)
class FeatureValue:
    available: bool
    value: Any = None
    reason: str = ""


@dataclass(frozen=True)
class TechnicalFeatureDefinition:
    feature_id: str
    version: str
    display_name: str
    family: str
    parameters: Mapping[str, Any]
    required_fields: tuple[str, ...]
    minimum_warmup: int
    supported_horizons: tuple[str, ...]
    supported_instrument_classes: tuple[str, ...]
    implementation_reference: str
    status: FeatureStatus

    def __post_init__(self) -> None:
        if not self.feature_id or not self.version or not self.display_name or not self.family:
            raise ValueError("feature identity and classification are required")
        if self.minimum_warmup < 1 or not self.required_fields or not self.supported_horizons:
            raise ValueError("feature inputs, warmup and horizons are required")
        if not self.implementation_reference or not isinstance(self.status, FeatureStatus):
            raise ValueError("implementation reference and status are required")
        if self.feature_id.endswith("_legacy_v1") and self.status is not FeatureStatus.LEGACY:
            raise ValueError("legacy feature IDs must have LEGACY status")
        if self.status is FeatureStatus.CANDIDATE and "candidate" not in self.implementation_reference.lower():
            raise ValueError("candidate implementations must be explicitly identified")


Calculator = Callable[[Sequence[float]], FeatureValue]


class TechnicalFeatureRegistry:
    def __init__(self, definitions: Sequence[TechnicalFeatureDefinition] = ()) -> None:
        self._definitions: dict[str, TechnicalFeatureDefinition] = {}
        self._calculators: dict[str, Calculator] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: TechnicalFeatureDefinition, calculator: Calculator | None = None) -> None:
        if definition.feature_id in self._definitions:
            raise ValueError(f"duplicate feature ID: {definition.feature_id}")
        if definition.status is FeatureStatus.LEGACY and calculator is None:
            raise ValueError("registered legacy features require a reference calculator")
        if calculator is not None:
            self._calculators[definition.feature_id] = calculator
        self._definitions[definition.feature_id] = definition

    def definition(self, feature_id: str) -> TechnicalFeatureDefinition:
        return self._definitions[feature_id]

    def definitions(self) -> tuple[TechnicalFeatureDefinition, ...]:
        return tuple(self._definitions[key] for key in sorted(self._definitions))

    def compute(self, feature_id: str, values: Sequence[float]) -> FeatureValue:
        if feature_id not in self._calculators:
            raise ValueError(f"feature has no calculator: {feature_id}")
        return self._calculators[feature_id](values)

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))
