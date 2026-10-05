# R1 local backtest research integration

Completed locally on 5 October 2026 under ADR 0051. The owner accepted B5 as partially closed: software verified, real-data acceptance pending. The Trading Strategies dashboard now displays a dated, read-only evidence summary. This is a report interface, not an engine or provider execution interface.

## Operating interface

Run the offline exporter from the repository using the Python environment already configured for this project:

```powershell
python scripts/export_local_backtest_dashboard.py --status <B5-status.json> --comparison <source-comparison.json> --reference <independent-observed-price-cash-reference.json> --output <report-directory>/dashboard-summary.json
$env:LOCAL_BACKTEST_REPORT_DIR = '<absolute-report-directory>'
```

Set that environment variable in the process that runs the dashboard. Existing installations need the new code and this configuration; this milestone does not deploy or restart the main or hosted dashboard. The reviewed localhost preview uses the actual dashboard template and static assets, with other services explicitly unavailable.

GET `/api/v1/local-backtest/research-summary` reads only the fixed summary filename. Refreshing the panel repeats this read. Missing configuration returns NOT_CONFIGURED; missing, oversized, malformed or changed content returns UNAVAILABLE without paths or exception details. Unknown fields, unsupported outcomes, noninteger counters and invalid comparison denominators are refused. POST is unavailable.

The exporter requires the owner-approved partial-close receipt, a conditional reference with no admission/replay, and its matching comparison hash. It projects only the fixed schema, dates, bounded counts and input hashes. It is specific to the dated Sasol pilot. No provider requests, database writes, account access, selection changes or broker actions occur. SHA-256 detects accidental content changes; it is not an authenticity signature. Keep the configured directory under trusted local control.

## Meaning of the display

The dated B5 evidence records 921 software tests, 54 protected checks, 36 conditional accounting scenarios and 72 directional fee checks. Iress intraday OHLC matches daily prices on 23/23 dates, while volume matches 0/23. The capture contains 391 bars and 368 cost/capacity sensitivity cases. Zero real-data trades are admitted; these conditional calculations do not establish strategy performance.

Remaining acceptance gates are RAW/adjustment and corporate-action evidence, intraday volume/bar-timing semantics, and an independent engine trade/cash audit after admissible input exists. IG historical access and entitlements must be tested in its runtime separately. Integration alone does not establish access.

## Verification

Five focused tests cover export provenance and owner acceptance, response safety, tamper/schema refusal, unavailable states and the read-only route. The full safe suite passed 926 tests in 87.712 seconds; all 54 protected artifacts passed. Browser review confirmed the Trading Strategies panel, displayed counts, explicit zero-admission state, remaining gates and saved-evidence refresh. No engine behavior changed, so prior engine mutation results remain historical evidence rather than a new R1 run.
