# Sector and Instrument Profiles

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
