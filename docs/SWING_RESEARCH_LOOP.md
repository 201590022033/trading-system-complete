# Daily Swing research loop — actual placement and boundaries

Reviewed 5 October 2026. See [current state](CURRENT_STATE.md), [profile versions](research/STRATEGY_PROFILES.md) and [the proposed six-family workflow](research/SIX_SWING_HYPOTHESES.md).

## Collection and durable state

`scripts/collect_swing_data.py` collects real completed Yahoo daily histories, validates identity/timeframe/ZAR and rejects estimated inputs. It retains ignored dated/latest raw files under `runtime/local-swing-data/` and uploads a bounded authenticated snapshot to `POST /api/v1/swing-research/datasets`. The current collection contains 21 chart histories: 17 active cash shares and four ETFs. Data bodies and upload secrets are never Git artifacts.

The configured Windows task **Trading System Local Swing Daily Data** runs at 07:30 SAST with start-when-available behavior and a 20-minute limit. It requires the PC powered on and the user signed in. Raw daily bars are archived once per UTC collection day. Upload failure is visible and does not authorize invented replacement data.

Railway stores snapshots/proposals/runs through the existing append-only research ledger under `swing-research-v1`. `SWING_DATA_SOURCE=LOCAL_UPLOAD` is active, so the scheduled paper-input path fails closed without usable uploads. Independent dashboard quote/chart and source-news reads can still call their existing providers.

## Bounded cloud comparisons

Railway's worker runs `0 6 * * *`, at 08:00 SAST, and exits after bounded work. The web service and PostgreSQL remain reachable/durable. Swing research is enabled. One UTC-day cloud attempt is reserved before generation; retries reuse immutable proposals and cached datasets.

Swing 1.3.0 freezes a bounded proposal for relative volume (1/1.2/1.5), RSI ceiling (65/70), and 3/4/5-session hold. It compares against 1.2.0 on chronological real-data slices: at least 130 observed sessions, training before the final 47 sessions, six purged sessions and 40 held-out dates. The model sees training context and past training comparisons, never held-out outcomes. Reusing the holdout is marked `NOT_ELIGIBLE_PROSPECTIVE_WALK_FORWARD_REQUIRED`.

The first real proposal was 1.2 volume, RSI 65, hold four. Both baseline and candidate produced zero closed holdout samples and 680 blocked/unresolved checks. Incomplete source OHLC prevented proof of performance. This is not 680 losing trades, continuous model-weight learning or an adopted strategy.

## Local news research

When `WEEKLY_NEWS_RESEARCH_ENABLED=1`, a successful daily upload precedes the bounded local weekly-news scan. Local Ollama interprets retrieved article/brief context, saves raw responses/receipts and delivers validated derived cases through an idempotent outbox. See [weekly news guide](research/WEEKLY_NEWS_RESEARCH.md). Current accepted cases are single-publisher and unflagged; no priority boost or historical sample was earned.

## Difference from the requested next loop

Today's uploader sends all configured charts and the 1.3.0 technical comparison runs on Railway. The owner's next target moves full six-family technical backtests/calculations to the home PC, retrieves verified historical events, refines admitted daily triggers with real 30-minute bars and uploads selective investigations. That complete radar/backtest loop is still proposed, not installed. Cloud availability does not compensate for missing local data or an offline PC.

Alpha Vantage scheduled calls are off both locally and on Railway. IG JSE daily history remains entitlement-blocked. Display estimates never enter replay. Default canonical profile 1.0.1, paper safety controls, and disabled Live execution remain unchanged.
