# OI3 public market and sentiment feeds

The root dashboard automatically loads six quote cards, selected-stock and JSE
All Share proxy charts, and the existing SA/global sentiment scanner. Click a
quote or select an instrument; choose intraday (five-minute bars), one month,
three months or one year. Chart hover shows the dated close and volume. News can
be filtered to the selected instrument; macro scores, source links, timestamps,
asset tags and AI/keyword provenance are visible.

## Contracts and refresh

- `GET /api/feed/market/<instrument>?period=1d|1mo|3mo|1y`: whitelist canonical
  instruments/aliases plus `JSE` (`^J203.JO`, the existing historical index proxy).
- `GET /api/feed/news`: shared retained `MacroSentimentScanner` report, with
  per-source availability, per-item `llm_used`, and actual analysis method.
- Both return `state`, `data`, `last_attempt`, `last_success`, `refreshing`,
  `refresh_seconds`, `source` and a sanitized `error`.
- HTTP reads schedule at most one background job per key and return immediately.
  Intraday refresh is bounded to 60 seconds; daily history and news to 300 seconds.
  The browser checks every 10 seconds while visible with auto refresh enabled.
  A pending explicit chart/news request polls every two seconds until completed,
  including when periodic auto refresh is paused. Refresh buttons respect server
  cache intervals; multiple tabs do not multiply upstream calls.
- Provider failure retains last-good chart data and its timestamp as `STALE`.
  Failed news refresh preserves a bounded, deduplicated 100-headline archive.
  Empty feeds are `EMPTY_OR_UNAVAILABLE`, never asserted to be healthy/empty.
- Headline previews appear before slow AI requests complete. Up to eight new
  items per scan use the configured existing Ollama path; duplicate headlines do
  not consume the AI budget. Every item has an explicit AI or keyword label.

## Opportunity discovery

`GET /api/opportunities` is separate from the six-instrument baseline
watchlist. It scans the broader public JSE universe represented by the adapter,
calculates current Yahoo 20-session momentum and RSI, and overlays matching
current-news ticker impacts when available. Results carry `TECHNICAL_ONLY` or
`NEWS_AND_TECHNICAL` state and are research-only. Missing bars, unavailable
providers and insufficient evidence remain visible; no result is an order or a
claim of predictive accuracy.

## Data interpretation

Yahoo currency metadata determines conversion: confirmed `ZAc` is divided by
100 and shown as `ZAR`; unknown currency stays unknown. Index values are points.
Charts are unadjusted public close bars. Percentage change spans the selected
chart range, not necessarily the current trading session. Daily timestamps are
session dates and five-minute timestamps are bar starts. Bars older than 30
minutes (intraday) or four days (daily) are `STALE_OR_MARKET_CLOSED`; this is not
an exchange-calendar determination. No verified real-time tick entitlement is
asserted. The confidence freshness gate requires explicitly verified freshness.

The analysis panel still uses the HR7 historical technical benchmark. Its market
component consumes the same current quote cache; its news component consumes
selected-instrument impacts from the shared scanner. These components disclose
their independent dates/states. The UI labels this mixed context. No adaptive
strategy was promoted and broker writes remain disabled.

## Run and verify

Run `.venv/bin/python -m pip install -r requirements.txt`, then
`.venv/bin/python app.py` and open forwarded port 5000 at `/`.
`ollama` is now an explicit runtime dependency. Existing `OLLAMA_API_KEY` /
`OLLAMA_CLOUD_MODEL`, or the local Ollama service and `OLLAMA_LOCAL_MODEL`, supply
AI sentiment. Never paste keys into chat or commit local credential files.
Without a usable model the news feed remains available with keyword labels.
NewsAPI remains optional and uses the scanner's existing environment configuration.
The default local model is `llama3.2:3b`; set `OLLAMA_LOCAL_MODEL` only when a
different model has been installed with `ollama pull`.

Offline regression:

```bash
python -m unittest test_dashboard_feeds test_oi2_operational test_ui_prototype test_provider_interfaces test_legacy_scoring
```
`scripts/check_dashboard_browser.py` is an explicitly opt-in real-provider smoke
check requiring a running app and separately installed Playwright/Chromium. It
loads public sources and the configured model through the application.

The new adapter uses the documented
[yfinance Ticker.history interface](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html).

## Remaining runtime dependency

The 2026-09-05 smoke check returned real Yahoo bars and Moneyweb headlines, but
no successful AI analysis. SENS returned HTTP 403 and NewsAPI was not
configured. Identifying/restoring the owner's former AI provider is still pending;
these are not grounds to claim an operational AI feed.
