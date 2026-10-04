# ADR 0040 — Cached, conditional Alpha Vantage cash-bar repair

Date: 2026-10-04. Status: implemented; actual JSE coverage awaits private-key probe.

Owner requests a free-tier fallback only for invalid/missing Yahoo data and
private API setup on both local computer and Railway. IG equity history remains
permission-denied. The third-party JSE explorer is not a coverage source: its
public code supports simulated fallback and its proxy returned 404.

Add one direct read-only Alpha Vantage client. Only SYMBOL_SEARCH and compact
TIME_SERIES_DAILY are admitted. Never guess .JSE symbols: unique search identity
must match Yahoo's JSE ticker stem, South Africa region, ZAR and Equity/ETF type.
Daily response symbol and Africa/Johannesburg timezone must match. OHLCV must
be finite, nonnegative volume, positive internally consistent prices, and a
completed session. No US ADR, CFD, cent/rand scaling guess or synthetic data.

Repair only invalid completed bars within Yahoo's trailing 100 sessions. If all
bad dates precede that window, make no API calls. For each replacement, require
the same date and exactly matching Yahoo close (numeric tolerance 1e-8); replace
the whole OHLCV record with provider lineage. Good Yahoo rows remain byte-equivalent.
Older holes stay unresolved. Free compact data cannot supply 20 years or safely
repair an entirely missing Yahoo chart without independent identity/unit checks.

The paper host computes repaired full-history technical features before compacting
60 retry bars. Only when actual repairs occur, freeze a separate swing_charts
map for technical labels and policy replay. Original charts, ranking inputs,
account fills, risk and historical compact report stay unchanged. Repair metadata
is in feature snapshots and bar hashes; immutable decisions/observations still
win on retry or later provider revisions. Repair does not optimize/promote rules.

Reuse existing locked, both-backend paper-account JSON persistence in the isolated
market-data-alpha-vantage-v1 namespace for cache and budget; never alter trading
cash/config. Reserve requests under lock BEFORE network; failures count and
in-flight cache prevents duplicate requests. Cache daily series 24h, mappings and
unsupported symbols 30 days, network failures one hour. Provider Note/Information
blocks all new symbols 24h. No waits/retry storms; exhaustion is explicit.
Cached data cannot be used before its retrieval time. Daily scan priority rotates
durably across instruments so the minute cap cannot starve later symbols.

Production budget is conservatively 20 requests per rolling 24 hours and five
per rolling minute, shared by web/worker using the same repository. Reserve five
calls for the local manual probe, whose persistent local cache has its own
five-call budget. Local scheduled fallback defaults OFF. Calls outside this
integration are not observable; use a dedicated key and do not enable multiple
independent scheduled deployments without sharing/reallocating the budget.
The provider's free cap is 25/day. Five/minute is the owner's conservative guard;
current support documentation does not state that minute allowance.

Private setup extends the prior Ollama PowerShell pattern: hidden SecureString
prompt, preserve .env privately, verify git ignore, Railway key via stdin, suppress
secret-bearing output, explicit project/environment/services and skip deployments.
Only non-secret completion flags are written to ignored runtime cache. Scheduled
local calls remain off; Railway ENABLED=1 takes effect on a later deployment.
No broker mutation, deployment or schema migration is performed by setup.

Sources: https://www.alphavantage.co/documentation/#daily and
https://www.alphavantage.co/support/ (verified 2026-10-04). Full daily history and
Daily Adjusted require premium access; raw daily compact is the free request used.
