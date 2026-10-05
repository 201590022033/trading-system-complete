# B5 autonomous continuation — 5 October 2026

The user authorized autonomous full B5 completion. Data acquisition, reconciliation, official daily-calendar capture, opt-in fee implementation and available verification are complete for this continuation. **Full B5 external acceptance is not complete:** zero real-data windows/trades are admitted. No following milestone or dashboard integration was activated.

User-facing evidence is in the local chat directory `C:\Users\Deon\Documents\Codex\2026-10-05\local-swing-backtest-engine\outputs\b5-completion\`. `B5-continuation.md` explains findings; `B5-status.json` lists resolved/unresolved gates; `verified-calendar-window.json` records the official pilot dates and document hashes; `cash-cost-capacity-stress.json` holds 368 cost/capacity cases; `checksums.json` binds evidence and code. Frozen raw price comparisons remain in its sibling `data-checks/` and IRESS captures in `price-data-search/`. Downloaded PDFs remain local runtime evidence, not source-controlled redistribution.

## Resolved

- Official JSE broad equity calendar/hours were accessible through normal Codex browser navigation and supported link downloads. Notice 380/2025 pages 2–3 visually confirms 24 September as the sole holiday in the pilot window; the hours PDF states 09:00–17:00 SAST. All 23 expected dates match the captured daily records.
- OST high/low/close/volume equals IRESS daily on 23/23 dates; Sharenet matches all ten available dates. Price units are explicitly cents in OST headings. IRESS intraday aggregated OHLC matches its daily reference on all 23 dates.
- Native IRESS export UTC timestamps and OHLC match 177 rendered rows at the SAST offset. Native export omits volume; table captures remain the volume source. This corroborates timezone alignment but not start/end labeling or interval eligibility.
- Direction-aware published OST fees now work in isolated replay and affordability sizing. Existing diagnostic formula is reused. Exact account tier, historic applicability and invoice rounding remain unverified. See ADR 0049.

## Remaining acceptance evidence

Intraday sums differ from daily totals on 23/23 dates, most markedly 22 September (3,567,845 versus 11,844,823 shares). Distinct on-/off-book or reporting eligibility is a plausible explanation, not a verified provider definition. Do not repair bars, distribute residual volume or ignore it in an activity strategy.

Issuer information supports no FY26 interim/final dividend, and Yahoo returns no window actions. That does not certify a complete split/rights/capital/action ledger or the chart's adjustment policy. The detailed ShareData company calendar is Premium gated; a signed-in free account is insufficient. The broker's 2016 charting guide supplies basic controls but not the required volume filter or bar convention. The active ViewPoint chart later rendered blank; no new terms were accepted to launch another session.

Current rates and post-hoc daily capacity stress are sensitivities, not dated historical invoices, bid/ask, queue or fill receipts. Maximum tested position is below 0.025% of daily volume; this is insufficient to assert liquidity at a particular close. Proposed reconstructed close-plus-delay availability remains distinct from actual October receipt and is not point-in-time availability. IG credential presence was checked without emitting values; both available .env files are incomplete, and no authentication/history request was made. Alpha/JSE mapping and own FX/gold executable contracts remain unresolved.

No admission bypass or downgraded evidence requirement was added. Supply complete provider action/adjustment and interval/volume definitions and the missing execution contracts; then create a new immutable manifested slice and independently reconcile its hypothetical trades, cash and equity. Unsupported markets can remain explicitly blocked under the existing scoped-acceptance contract, but the currently missing cash slice evidence cannot be self-certified.

## Verification and reuse

26 focused tests pass; 921 offline tests pass (87.851s); all eight disposable defects killed; 54 protected artifacts pass. Existing equity/FX/gold examples retain identical semantic hashes. The cost/capacity report reproduces byte-identically offline. No push, deploy, hosted configuration, default strategy, provider collector or external account change.

```powershell
& $taskPython scripts/stress_local_b5_cash.py --comparison <frozen-source-comparison.json> --output <new-report.json>
```

Inputs are frozen observed comparisons; the script performs zero network requests. Do not use observed end-of-day volume as a before-entry sizing feature. `OSTCashShareCosts` is opt-in; generic `Costs` defaults are unchanged. Reports remain assumption limited until the separate admission gates pass.
