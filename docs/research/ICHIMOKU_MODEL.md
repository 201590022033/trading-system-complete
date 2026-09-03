# Point-in-Time Ichimoku Model

`ichimoku_features.py` implements full deterministic Ichimoku context in
research/shadow mode. Default periods are 9/26/52 with displacement 26 and a
78-OHLC-bar minimum warm-up.

## Displacement semantics

- Tenkan and Kijun at decision time use only trailing highs/lows through `t`.
- The cloud visible at `t` uses Senkou values calculated from data ending at
  `t-26`; it is not recalculated from today's window.
- The future cloud uses today's Tenkan/Kijun and 52-bar midpoint because that
  projection is mathematically known at `t`. Its field names explicitly say
  `known_at_t`.
- Chikou context compares today's close, plotted back 26 bars, with the already
  known price at `t-26`. It never reads `t+26`.

## Features

The model returns Tenkan, Kijun, current and known-future Senkou spans, price
above/inside/below cloud, cloud thickness, future-cloud direction, TK spread,
Kijun distance, Chikou relationship, cloud breakout, TK cross and strength, and
three-way regime consistency. None is an unconditional signal.

Capability and future-mutation tests cover OHLC gating, 78-bar warm-up, visible
versus projected cloud displacement, and invariance to changes after the as-of
index. Asset/regime/horizon effectiveness is deferred to HR7/HR8; no assumption
from other markets is transferred to JSE equities, USD/ZAR, gold or Brent.
