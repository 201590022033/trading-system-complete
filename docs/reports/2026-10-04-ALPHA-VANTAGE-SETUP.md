# Alpha Vantage free-key setup and guarded Yahoo repair

Starting clean master f572634e8fe88f02180aabb25c7ff2c74b10ec68.
Baseline 786 safe tests pass. Final 56 focused tests and 807 full safe tests pass
(56.282 seconds). All 54 protected artifacts unchanged. JavaScript syntax,
PowerShell parser and diff-whitespace checks pass. Native PostgreSQL/browser
visual acceptance was not run; repository-backed cache/retry tests use SQLite.

Owner chose BOTH local and Railway. A private hidden prompt saved the key in the
ignored local .env. Initial Windows policy/profile loading blocked the script;
reopening without profiles with a process-only policy override resolved it.
Railway's PowerShell wrapper then treated a deprecation warning as a terminating
error. Setup now uses the native/.cmd CLI, suppressed native output and exit-status
checks. Saved key was privately reused with UseSavedLocalKey, without a second
prompt. CLI updates succeeded for production web and trading-worker, each with
ALPHA_VANTAGE_API_KEY and ALPHA_VANTAGE_ENABLED=1, using stdin and --skip-deploys.
Local scheduled calls stay OFF; local explicit coverage probe is available.
Non-secret setup receipt confirms both destinations and no setup-triggered deploy.

Five local coverage requests were reserved in the persistent five-call cache:
SOL, NPN and STX40 symbol searches did not yield unique matching South African
ZAR listings. Company-name Sasol search returned SASOF/SSL (US/USD) and SAO.FRK/
SAOA.FRK (Frankfurt/EUR), never accepted as JSE substitutes. The Naspers name
request returned provider Information, surfaced as PROVIDER_LIMITED_OR_PREMIUM_REQUIRED
without persisting the raw message. No further live provider requests were made;
no Alpha Vantage JSE bars or volumes were obtained. This is not proof of universal
absence: actual support remains UNVERIFIED. The guarded fallback will not invent
coverage or use another exchange's listing.

Implemented: AlphaVantageClient in application/opportunities/alpha_vantage_data.py;
worker composition and frozen-shadow replay in paper_host.py/paper_loop.py;
Portfolio repair display; .env.example; PowerShell setup and safe local probe;
21 new focused tests; ADR 0040, architecture, roadmap and setup runbook.

Production uses Yahoo first. Good data, web reads, duplicate sessions and frozen
retries consume no provider calls. Invalid recent bars trigger cached discovery
and daily compact requests, subject to exact JSE symbol/session/raw OHLCV/close
checks. Repairs are full same-session bars with provenance, used ONLY for separate
shadow features/labels/policy paths. Valid Yahoo rows, ranking closes, paper fills,
account/risk, profile versions and weights stay unchanged. No new schema, synthetic
bars, broad historical relabelling, broker mutations or LIVE execution.

Production shared-repository cap is 20 requests/rolling 24h and five/rolling minute,
leaving five for the separately capped local probe. Reserve-before-network and
in-flight caching protect concurrency/restart; daily scan order rotates. Daily
series cache 24h, search/unsupported 30 days, failure one hour, provider limits
24h across symbols. Other applications using the same key still consume provider
quota; local scheduled fallback stays off to avoid competing independent budgets.

Free daily history covers up to 100 observations, not 20 years. Old invalid Yahoo
rows remain unresolved and cannot be dropped to manufacture an ATR-ready history.
Entire missing Yahoo charts remain blocked without independent price verification.
IG JSE equity-history 403 remains an external entitlement issue.

Next: verify actual JSE coverage with Alpha Vantage support or a later quota-safe
probe. If unsupported, obtain verified OST/IRESS/JSE cash OHLCV export/API access.
Do not purchase premium on the strength of the third-party explorer's simulation.
Deployment is authorized by the owner's earlier push-and-deploy instruction;
deployment evidence is recorded separately after success.
