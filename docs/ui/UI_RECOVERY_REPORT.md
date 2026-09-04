# UI Recovery Audit

Date: 2026-09-04
Audit baseline: `a1f8fbf` (the request named `d9bf5b0`, but it was not HEAD)

## Outcome

The reported complete dashboard cannot be recovered from this repository.
No committed, deleted, renamed, unreachable or archived UI contains the landing
page, separate news/technical controls, OST panel, 30-check component, analysis
dashboard and BUY/SELL/HOLD panel described by the owner. Under the recovery
stop condition, no replacement was reconstructed from memory.

The most complete committed UI here is the current OI1 `app.py` at `a1f8fbf`.
It is an expanded version of the simulated ticker, not the reported historical
application. The oldest `app.py` is commit `332666a`; its parent has no `app.py`.
Consequently, repository evidence does not support the claim that HR10 removed
the complete dashboard. The likely source is an earlier/external `rania321`
project or an uncommitted file that was never imported into this Git history.

## Inspected evidence

- `git log --all --oneline --decorate --graph` and path history for `app.py`,
  `generate_app.py`, templates and static assets.
- Every committed `app.py`: `332666a`, `a2376fe`, `d9bf5b0`, `a1f8fbf`.
- Diffs between those versions and the absence of `app.py` in `332666a^`.
- Deleted/renamed file history and semantic `git grep` across reachable commits.
- All unreachable blobs reported by `git fsck --full --no-reflogs`.
- `logs.zip` inventory; it contains Codespaces logs, not application UI assets.
- Current protected `generate_app.py`, its worktree diff and its committed history.
- Current backend modules, routes and merge/quick-start documentation.

No `templates/`, `static/`, standalone dashboard HTML/JS/CSS, or historical
multi-page Flask route exists in any inspected commit. One unreachable blob is
only a trivial test HTML page.

## Feature archaeology

| Feature | Current UI | Last known implementation in this repository | Commit/file | Backend still exists? | Recovery action |
|---|---|---|---|---|---|
| Original landing page | Simulated OI1 decision/ticker page | Not found | None | Not applicable | Obtain original project/export/screenshot |
| Live iteration/data | One-second simulated Socket.IO random walk | Same simulated ticker introduced here | `332666a:app.py` | Yahoo polling and Finnhub fetchers exist, but are not UI-wired | Do not label live; characterize provider before wiring |
| Scan Market News | Missing | Not found | None | Yes: `MacroSentimentScanner`, NewsAPI, Moneyweb/SENS collectors; network/credential constraints vary | Recover original UI contract or design later with explicit invocation |
| Technical Indicators scan | Missing | Not found | None | Yes: legacy `JSESignalEngine.scan_market`, pipeline indicators and research modules | Recover original UI contract; keep HR9 separate |
| Standard Bank OST section | Missing | Not found | None | Yes: `StandardBankOSTAdapter`, local browser worker/client; manual login and never-submit preparation | Recover only with original UI; preserve login/MFA boundary |
| 30-step confidence checker | Missing | Not found | None | No 30-check backend | Documentation mentions a hardcoded 30-step simulation, not 30 confidence checks | Request screenshot/source; do not invent semantics |
| Analysis dashboard | Missing | Not found; `templates/dashboard.html` appears only as a future plan | `MERGER_STRATEGY.md` | Decision records exist in `MergedSimulation` | Obtain original dashboard source |
| BUY/SELL/HOLD area | OI1 fabricated rejected BUY card only | Not found as historical UI | None | Yes: legacy `signal_pipeline.py` and `merged_simulation.py` generate decisions | Do not substitute rejected HR9; recover original UI contract first |

## `generate_app.py` finding

`generate_app.py` is not an application generator. The original committed
version searched for a dashboard HTML file, then sent that HTML to an external
LLM for a JavaScript memory-leak audit. Later/current work changed it to import
`INDEX_HTML` from `app.py` and corrected API configuration/client usage. It
does not contain the reported dashboard and never generated `app.py`.

The current uncommitted changes are valuable security/correctness work and were
left untouched. Audit also found a credential-like literal in the historical
committed version. Its value is intentionally not reproduced here. Treat it as
compromised: revoke/rotate it and separately decide whether to purge Git history.
No history rewrite was attempted.

## What changed in committed `app.py`

- `332666a`: created the only Flask UI—a self-contained simulated JSE ticker,
  `/api/snapshot`, `/health`, and one-second random-walk Socket.IO broadcasts.
- `a2376fe`: changed only `generate_app.py`; `app.py` stayed identical.
- `d9bf5b0`: retained the ticker and added truthful simulated/research/not-live labels.
- `a1f8fbf`: added the rejected demo decision card, responsive layout, local
  feedback and `/api/demo-suggestion`; it did not delete earlier UI routes.

There is therefore no identifiable disappearance commit for the seven reported
feature groups inside this repository.

## Actual data states

- **Simulated:** everything rendered by `app.py`; random in-memory prices,
  synthetic bid/ask/volume and local wall-clock display.
- **Historical:** frozen HR2–HR10 research artifacts; not connected to Flask.
- **Delayed/current external:** Yahoo Finance fetch paths can retrieve public
  current/history data, subject to availability and provider semantics; not UI-wired.
- **Potentially live:** Finnhub and authenticated OST paths exist but need keys,
  subscriptions/login and validation; not UI-wired and not exercised in this audit.
- **Live in current UI:** none.

## Recovery prerequisite

Provide any one of: the original repository/branch/ZIP; the missing HTML,
templates or Flask app; a screenshot; or an exact external commit/repository
reference. With that evidence, restore the old UI additively and retain OI1's
state labels, stale/rejected gates and no-live-write boundary.
