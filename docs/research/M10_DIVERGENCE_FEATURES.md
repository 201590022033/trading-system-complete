# M10 — Divergence & Disagreement Features

## Status

**COMPLETE — 2026-09-09**

M10 adds the unweighted, research-only `divergence-v1` feature family. It
measures disagreement explicitly instead of allowing opposing signals to look
like an absence of evidence. It does not claim predictive usefulness.

## Definitions

For causally available legacy states in `{-1, 0, +1}`:

- `active_signal_count = positive + negative`
- `directional_balance = (positive - negative) / active`, when active exists
- `disagreement_ratio = 2 * min(positive, negative) / active`, when active exists
- `agreement_strength = max(positive, negative) / active`, when active exists
- `bullish_intensity = positive / active`; `bearish_intensity = negative / active`
- `dominant_direction` is the sign of the larger directional count
- `dominance_margin = abs(directional_balance)`
- `signal_dispersion` is population standard deviation of supplied compatible
  continuous values
- `evidence_coverage = causally available inputs / configured expected count`

The output retains positive, negative, neutral and unavailable counts. Equal
positive/negative evidence is `HIGH_DISAGREEMENT`; one-sided evidence with a
residual opposing signal is `DOMINANT_WITH_CONFLICT`; one-sided evidence is
`HIGH_AGREEMENT`; insufficient active evidence is `LOW_EVIDENCE`.
Unavailable inputs are not neutral inputs.

## Pair, group and horizon contracts

`pairwise` and `grouped` expose the same versioned summary for existing causal
input families such as technical versus macro or trend versus momentum. No
synthetic news or macro history is created. Instrument and horizon identity are
retained, including the existing separation between intraday-duration and
daily-session horizons.

Price/indicator pivot divergence is not implemented in M10: the repository does
not yet have a causal pivot-confirmation contract, so no hindsight-selected
pattern is introduced.

## Causality and provenance

Only inputs with `available_time <= evaluated_at` contribute to counts, metrics,
coverage or lineage. Future observations are excluded entirely and cannot alter
an earlier result. Every output records feature IDs, feature versions,
availability timestamps, feature version, evaluation time, instrument, horizon,
configuration version and optional regime version/state metadata.

Regime context is descriptive only; it does not alter divergence calculations.
No learned HR8/HR9 weights are reused. Minimum evidence is configuration, not a
universal threshold.

## Runtime and evidence boundary

The feature family is not connected to scoring, opportunity ranking, TradePolicy,
risk, GUI, Railway, broker execution or portfolio logic. No profitability
optimization, HR10 rerun or historical artifact regeneration occurred. The
local suite passes 296 tests and all 39 immutable research artifacts remain
unchanged. Predictive usefulness remains unknown and requires later causal
evaluation by instrument, horizon, regime and feature family.
