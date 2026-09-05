# OI3 restoration and verification — 2026-09-05

## Delivered

The dashboard now loads real public quote cards, selected-stock and JSE All
Share proxy charts, and retained news/asset sentiment instead of hiding price
history and headline arrays. Both feeds refresh independently. The existing
MacroSentimentScanner is connected, including its model path, progressive
headline preview, bounded AI budget and explicitly labelled keyword fallback.

Added dated bars and confirmed cents-to-rand normalization to the existing Yahoo
adapter. Preserved its legacy scalar methods, research artifacts and signal
weights. Historical technical analysis stays explicitly separate from current
market/news context. No executable suggestion or broker write was enabled.

## Verified

- 114 safe offline unit/regression tests passed across 27 modules.
- Excluded the existing standalone network/credential/model probes:
  `test_cloud`, `test_ost_login`, `test_reddit`, `test_sentiment`,
  `test_llm_sentiment`. Model success/fallback is tested with mocks, not paid calls.
- Chromium against the actual port-5000 app rendered two charts, six populated
  quote cards and ten real Moneyweb headlines, with no JavaScript errors.
- Instrument/range changes, full analysis (30 returned gates), six-instrument
  scanner, and 390-pixel mobile layout passed browser checks.
- Browser-only fixtures verified cold chart loading while auto refresh is
  paused, selected-instrument news filtering, escaped external content, and
  retention of headlines after an HTTP failure.
- A browser test initially exposed a paused-refresh chart getting stuck on
  LOADING. Pending explicit requests now poll to completion; the regression passed.
- Actual Yahoo smoke: 64 Sasol daily bars and 65 JSE index daily bars. Intraday
  quote cards populated for all six configured instruments. Timestamps and
  market-closed/stale labels remain visible; this is not a real-time entitlement.
- Python compilation, JavaScript syntax and `git diff --check` passed.

## Still unresolved — milestone remains ACTIVE

No usable AI model connection was available in this runtime: real headlines
were keyword-scored, and no successful external AI summary is claimed. The
Ollama client dependency is installed in the project virtual environment and
added to requirements. The owner's previous provider/model has been requested.

Moneyweb RSS succeeded. The existing SENS public endpoint returned HTTP 403
with a challenge page; the application reports that source failure and makes no
attempt to bypass it. NewsAPI is not configured. Restoring those external
capabilities requires a usable configured service or permitted source access.

The implementation and available feeds are usable now, but the original request
for an operational AI news feed is not fully closed. No next milestone is active.

## Local use

Start `.venv/bin/python app.py`; open the root of forwarded port 5000. This server
was restarted with the restored build for review. Public caches and headline
retention are in memory and restart empty. See `docs/architecture/OI3_PUBLIC_FEEDS.md`
and ADR 0014 for behavior and limitations.
