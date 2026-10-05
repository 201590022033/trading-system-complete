# Sector and Instrument Profiles

## Current context — 5 October 2026

The original feature/profile contract below is retained as its delivery checkpoint. Existing regime and feature registries are reused. Separate Swing 1.1.0 now adds EMA20/50, Wilder RSI/ATR14, relative volume and independent 3/4/5-session labels; 1.2.0 adds cash-only daily policy replay and 1.3.0 adds bounded AI hypothesis comparisons. These are research lanes and do not change default ranking weights. Invalid OHLC, verified sector/FX/commodity context, actual event availability and prospective evaluation remain admission gates. The complete local six-family engine and 30-minute radar are proposed. See [current state](../CURRENT_STATE.md), [Swing readiness](../research/SWING_NARRATIVE_READINESS.md) and [document index](../DOCUMENTATION_INDEX.md).


---

`market_profiles.py` provides the versioned `profiles-v1` research context used
to classify instruments before adaptive feature weighting is introduced.

## Profile contract

Each immutable profile records a stable ID/version, sector, instrument type,
explicit macro sensitivity coefficients, and a `shadow_only` safety marker.
`ProfileRegistry` selects configured ticker mappings case-insensitively and
falls back to `single_stock` for an unknown ticker. The default catalogue covers
index derivatives, SSF/share CFDs, banks, gold miners, PGM and diversified
miners, Sasol/energy, retail/consumer, agriculture and USD/ZAR derivatives.

## Compatibility boundary

The coefficients moved out of `JSESignalEngine` reproduce its prior macro
overlay exactly: direct mentions remain `0.10`, relevant rand exposure remains
`+/-0.05`, gold exposure remains `0.08`, Sasol oil exposure remains `0.08`, and
the combined adjustment remains clamped to `+/-0.15`.

These coefficients are legacy characterization values, not validated causal
claims. Profiles expose context in signal metadata but do not alter fixed
technical/fusion weights, thresholds, or the default signal mode. Later
milestones may evaluate richer conditional channels in shadow mode.
