# Historical snapshot — docs/integrations/ALPHA_VANTAGE_SETUP.md

Archived during the 5 October 2026 reconciliation from `c2ef802`. The text below describes earlier checkpoint/design context, not current operational instructions. Original text is preserved; see [the current document](../integrations/ALPHA_VANTAGE_SETUP.md) and [current state](../CURRENT_STATE.md). Historical ACTIVE or planned labels do not activate work.

Original relative links belong to the original source location; use the current-document link above for present guidance.

---

# Alpha Vantage private setup and Yahoo repair

Run the reviewed setup from the repository in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/configure_alpha_vantage.ps1
```

Paste the private API key into its hidden prompt, never chat. This preserves other
local .env settings and saves ALPHA_VANTAGE_API_KEY on Railway production web and
worker using stdin and --skip-deploys. No service is restarted. ALPHA_VANTAGE_ENABLED
is 1 for future Railway deployments, 0 locally to reserve the manual-probe budget.
Only a non-secret setup receipt is written under ignored .cache. LocalOnly is an
optional switch. Do not run a variable-list command: it prints other secrets.
The execution-policy override applies only to this setup process; machine-wide
policy is not changed. If Railway fails after the local key is saved, rerun with
UseSavedLocalKey to privately reuse it without another prompt. The setup selects
the native/.cmd CLI and checks exit status, allowing harmless deprecation warnings
on Windows PowerShell 5 without printing native command output.

Validate one actual JSE instrument with the local project Python environment:

```powershell
python -m scripts.alpha_vantage_probe SASOL
```

The probe consumes up to two calls: symbol search and compact daily history if a
unique South African ZAR identity is found. Defaults use the ignored persistent
runtime/alpha-vantage-probe.db, capped at five calls/rolling day. Reuse this same
cache path; creating new databases bypasses that local budget. Output is safe
status, symbol, bar count and price basis, never key or raw error. Exit 0 means
history returned after identity gates; exit 2 means configuration/coverage/access
unresolved. If JSE_SYMBOL_UNVERIFIED, do not assume Alpha Vantage covers the JSE.

On the later code deployment, the daily Swing loader first acquires Yahoo charts.
No fallback calls occur for good data, duplicate completed sessions or web status
reads. Invalid recent bars trigger cached discovery/history; identical closing
prices, same session, raw OHLCV and verified search identity are required. Only
the separate research/shadow chart is repaired; ranking and cash simulator source
stay unchanged. Dashboard paper-model section reports repaired/unresolved dates
and coverage/quota states. Frozen input prevents refetching on worker retry.

Production makes at most 20 requests/rolling day and five/minute across its shared
repository, leaving five for local checks. Requests outside these clients still
consume the same provider key. Local scheduled fallback remains disabled; do not
enable additional independently budgeted clients without reassigning the cap.
Keys and downloaded series remain runtime data, not committed source artifacts.

Free TIME_SERIES_DAILY compact supplies up to 100 observations. It cannot repair
older invalid bars or deliver a 20-year dataset. Whole invalid/missing charts and
ambiguous prices remain blocked. There is no simulated or LLM-generated fallback.
