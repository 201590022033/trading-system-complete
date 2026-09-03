"""Versioned sector and instrument profiles for research/shadow context.

Profiles centralize ticker context that was previously embedded in the signal
engine.  Their macro sensitivities preserve the legacy overlay coefficients;
they do not enable adaptive weighting or change the production signal path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple


PROFILE_VERSION = "profiles-v1"


@dataclass(frozen=True)
class MacroSensitivity:
    factor: str
    weight: float


@dataclass(frozen=True)
class MarketProfile:
    profile_id: str
    sector: str
    instrument_type: str
    macro_sensitivities: Tuple[MacroSensitivity, ...] = ()
    direct_mention_weight: float = 0.10
    version: str = PROFILE_VERSION
    shadow_only: bool = True

    def macro_adjustment(
        self,
        macro_scores: Mapping[str, float],
        direct_score: float = 0.0,
    ) -> float:
        adjustment = self.direct_mention_weight * direct_score
        for sensitivity in self.macro_sensitivities:
            adjustment += sensitivity.weight * macro_scores.get(sensitivity.factor, 0.0)
        return max(-0.15, min(0.15, adjustment))


def _sensitivity(*pairs: Tuple[str, float]) -> Tuple[MacroSensitivity, ...]:
    return tuple(MacroSensitivity(factor, weight) for factor, weight in pairs)


DEFAULT_PROFILES: Tuple[MarketProfile, ...] = (
    MarketProfile("index_derivative", "broad_market", "index_future_or_cfd"),
    MarketProfile("single_stock", "general", "ssf_or_share_cfd"),
    MarketProfile("offshore_earner", "technology", "ssf_or_share_cfd", _sensitivity(("ZAR", -0.05))),
    MarketProfile("banks_financials", "financials", "ssf_or_share_cfd", _sensitivity(("ZAR", 0.05))),
    MarketProfile("gold_miners", "gold_mining", "ssf_or_share_cfd", _sensitivity(("GOLD", 0.08))),
    MarketProfile("pgm_mining", "pgm_mining", "ssf_or_share_cfd", _sensitivity(("ZAR", -0.05))),
    MarketProfile("diversified_mining", "diversified_mining", "ssf_or_share_cfd", _sensitivity(("ZAR", -0.05))),
    MarketProfile("energy_sasol", "energy", "ssf_or_share_cfd", _sensitivity(("ZAR", -0.05), ("OIL", 0.08))),
    MarketProfile("retail_consumer", "retail_consumer", "ssf_or_share_cfd", _sensitivity(("ZAR", 0.05))),
    MarketProfile("agri_linked", "agriculture", "ssf_or_share_cfd"),
    MarketProfile("usdzar", "foreign_exchange", "fx_future_or_cfd"),
)


DEFAULT_TICKER_PROFILES: Mapping[str, str] = {
    "ALSI": "index_derivative",
    "J200": "index_derivative",
    "NPN": "offshore_earner",
    "ABSPJ": "banks_financials",
    "GFI": "gold_miners",
    "IMPJ": "pgm_mining",
    "BHP": "diversified_mining",
    "SASOL": "energy_sasol",
    "SHPJ": "retail_consumer",
    "TFMJ": "retail_consumer",
    "JDIJ": "retail_consumer",
    "AFG": "agri_linked",
    "USDZAR": "usdzar",
    "USD/ZAR": "usdzar",
}


class ProfileRegistry:
    """Configurable, deterministic profile selection with a safe fallback."""

    def __init__(
        self,
        profiles: Iterable[MarketProfile] = DEFAULT_PROFILES,
        ticker_profiles: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._profiles: Dict[str, MarketProfile] = {
            profile.profile_id: profile for profile in profiles
        }
        self._ticker_profiles = {
            ticker.upper(): profile_id
            for ticker, profile_id in (ticker_profiles or DEFAULT_TICKER_PROFILES).items()
        }
        if "single_stock" not in self._profiles:
            raise ValueError("Profile registry requires a single_stock fallback")
        unknown = set(self._ticker_profiles.values()) - set(self._profiles)
        if unknown:
            raise ValueError(f"Ticker mappings reference unknown profiles: {sorted(unknown)}")

    def get(self, profile_id: str) -> MarketProfile:
        return self._profiles[profile_id]

    def select(self, ticker: str) -> MarketProfile:
        profile_id = self._ticker_profiles.get(ticker.upper(), "single_stock")
        return self.get(profile_id)

    def profile_ids(self) -> Tuple[str, ...]:
        return tuple(self._profiles)


DEFAULT_PROFILE_REGISTRY = ProfileRegistry()
