# ADR 0053 — Separate source recovery from admitted learning inputs

Date: 6 October 2026. Status: accepted for offline diagnostics.

## Context
R2 successfully connected collection and learning, but a fresh upload can contain old or invalid prices. On 6 October all 21 saved charts ended on 2 October and contained 876 invalid OHLC rows. Fresh Yahoo probes still omitted 5 October while exposing the unfinished 6 October bar. The existing collector correctly excludes that unfinished session. The previously captured IRESS SOL.JSE daily table contains 250 complete valid rows through 5 October. All 249 overlapping closes match Yahoo, while all 249 volumes differ. It provides actual alternative values for 19 invalid Sasol dates. STX40 has one invalid OHLC row and lacks the latest matching session.

## Decision
Reuse existing completion and real-OHLC validators in a bounded, offline readiness command. Convert the explicitly identified Sasol cents export to a separate single-source ZAR recovery artifact, retaining its content hash. Reject duplicate sessions, invalid prices, different product/units and any overlapping closing-price mismatch. Never patch high/low mathematically, mix volume feeds, upload this diagnostic artifact or substitute check time for historical availability. Keep old frozen decisions intact. This changes no collector, dataset API, strategy, worker, model budget or admission rule.

## Consequences
Sasol's missing numerical OHLC is recoverable: the separate file yields ATR/RSI/structure, but its latest relative-strength calculation remains blocked by an absent aligned benchmark session. RAW/action and volume semantics and historical availability remain unverified. Diagnostics can be repeated without providers or credentials. Coverage completion and outcome maturity remain separate facts; current live counts are 25 pending and zero matured per horizon. Existing causal tests establish implementation behavior, not actual matured returns.

## Renewed broker session continuation

The owner renewed OST login, permitting visible-table acquisition. A completed 5 October STX40 close resolves offline relative-return alignment. Extend the diagnostic command with an explicitly selected STX40 cash benchmark HLCV parser. Opens remain null; six inconsistent HLC envelopes in the latest 600 completed rows are recorded without repair. The existing benchmark calculation only consumes closes. This is not full OHLC recovery or dataset admission. Pairing gives complete numerical Sasol inputs; provider/source semantics and production wiring remain separate. Fresh SOL corroboration confirms 250/250 closes but only 247/250 highs and lows and 248/250 volumes. Retain both sources instead of blending.
