# M2 semantic drift register

| Version IDs | Existing location | M2 candidate/reference | Confirmed difference |
|---|---|---|---|
| `feat_rsi_legacy_v1` / `feat_rsi_wilder_v2` | `data_pipeline.py:SignalGenerator.calculate_rsi_signal` | `domain/features/technical.py` | Legacy uses a simple mean over the latest 14 deltas; candidate uses Wilder recursive smoothing. |
| `feat_sma_legacy_v1` | `data_pipeline.py:SignalGenerator.calculate_sma_signal` | `domain/features/technical.py` | Legacy is a 5/20 close SMA with a 0.1% deadband and returns a tuple; no candidate replacement is registered in M2. |
| `feat_breakout_close_legacy_v1` / `feat_donchian_break_v2` | `data_pipeline.py:SignalGenerator.calculate_breakout_signal` | `domain/features/technical.py` | Legacy compares the current close with prior closes in a 20-value window; candidate uses an explicit prior 20-close Donchian breach with a 21-value warmup. |
| `feat_stoch_close_legacy_v1` | `data_pipeline.py:SignalGenerator.generate_indicators` | `domain/features/technical.py` | Legacy is a close-only range oscillator; no OHLC stochastic replacement is wired into runtime. |
| `feat_macd_line_signal_v2` / `feat_bollinger_v2` | `research_indicators.py` | `domain/features/technical.py` | Existing research calculations expose MACD difference and Bollinger snapshot fields; candidates expose explicit line/signal/histogram and band objects. |

All candidate calculators are disconnected from scoring, dashboard routes, and
historical artifact generation. They are research/candidate definitions only.
