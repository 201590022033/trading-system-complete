# B5 real-source acceptance attempt — 5 October 2026

Owner authorized full B5 and flexible use of Yahoo, IG and Alpha Vantage. The bounded acquisition and available independent diagnostics are complete; **real-market engine acceptance remains BLOCKED**. No following milestone is active. This records actual observations and a cost sensitivity, not admitted replay trades or a strategy result.

## Frozen observations and provider findings

The explicit Yahoo query was `SOL.JO`, start `2026-09-01`, exclusive end `2026-10-03`, intervals `1d` and `30m`, `auto_adjust=False`, `actions=True`, `repair=False`, `raise_errors=True`, timeout 20 seconds. Daily retrieval: 2026-10-05 14:35:07 UTC; intraday: 14:36:52 UTC. Never re-download to reproduce the report: provider revisions must become new versions.

Daily: 23 bars, positive internally consistent OHLC, Johannesburg timezone, exchange JNB, equity type and explicit `ZAc` currency. Convert this daily cent quote to ZAR by exactly 0.01; volume is not multiplied. Source bytes SHA256 `e964cc97ad4d59ed34aa6d2f2db4f6e29992e2d324b691191f7ee74b6fc5b006`. Zero action entries were returned. That alone does not verify absence of all corporate actions.

Intraday: 368 observed 30-minute bars, 16 per observed date, timestamp starts 09:00 through 16:30 at UTC+02:00. Source bytes SHA256 `3f40960330d7174e26004a15712be44ba4c510b02b0229e210584a1f1c7c6ef0`. The raw intraday receipt did not capture its own currency/timezone metadata; the daily metadata is not silently copied into it.

All 23 aggregated intraday closes differ from the daily close, and all aggregated volumes are smaller. Some extrema also differ. Zero sessions reconcile all OHLCV fields. The report retains per-date differences in raw provider units. This is evidence of incomplete or different coverage, not proof of why the difference occurred; omitted closing phases are a plausible explanation. No bars, auction prices or volumes were synthesized. Even exact aggregation would not itself certify an exchange calendar or full fills.

Alpha Vantage was configured and queried through the existing governed client with its isolated local SQLite probe cache. The SOL search did not establish a JSE mapping. A full-name Sasol search returned SASOF/SSL in the US and SAO.FRK/SAOA.FRK in Frankfurt; none is an admissible substitute for JSE SOL. The shared local probe had five rolling request reservations, including existing reservations. No further FX/gold requests were made after exhaustion. This is a local conservative probe limit, not a claim that the provider's overall daily quota was exhausted. Scheduled Alpha Vantage was not enabled. Its [official documentation](https://www.alphavantage.co/documentation/) describes daily FX OHLC and gold histories, but prices alone would not verify broker contract costs, carry or margin.

IG credentials were incomplete in both the isolated checkout and original local source checkout. No IG authentication, market/history request or broker mutation was performed in this attempt. Existing historical entitlement failures remain historical; they do not establish current entitlement.

## Primary evidence and remaining gates

The [issuer's 1 September results announcement](https://www.sasol.com/sasol-sens/202609010005a-s602420) identifies JSE SOL, ISIN ZAE000006896, separately from the US ADR, and reports no final dividend. This supports identity and that dividend decision, but does not establish complete split/action or historical-universe coverage for the pilot window. Retrieved issuer HTML hash: `9d594e0dc6f375b2f3cfda1218f8e557bf9eca4027cd1c3a647433f0228173d2`.

The official [JSE calendar library](https://clientportal.jse.co.za/reports/trading-calendars) and [session documentation library](https://clientportal.jse.co.za/technical-library/trading-and-market-data-documentation) returned HTTP 403. Access controls were respected. Search-index references and government holiday dates are useful leads, not a frozen verified exchange schedule. Do not manufacture expected sessions from the observations.

| Gate | Result and exact remaining evidence |
|---|---|
| Identity and daily numeric quality | Partial: issuer SOL identity and provider units established; 23 observed daily bars numerically consistent |
| Expected sessions | BLOCKED: frozen official calendar, SOL trading segment and session times needed |
| Actions and historical universe | BLOCKED: complete dated action ledger and instrument/universe scope needed |
| Availability | Reconstructed download only. An explicit conservative historical availability contract can support scoped reconstructed research; no point-in-time claim is made |
| Costs/liquidity/full fills | Current public fees stressed; dated account tariff, actual quotes/closing coverage and a capacity envelope remain missing |
| Daily versus intraday | 0/23 complete aggregates reconcile; complete own-unit/session observations needed |
| Independent real trades | Zero admitted trades. Required trade, ledger and equity reconciliation cannot precede admission |
| FX/gold | Executable product prices and own calendars, conversion, contract, margin and financing evidence still required |

## Cost sensitivity, not historical execution acceptance

The [published OST cash-share tariff](https://onlinesharetrading.standardbank.co.za/standimg/OST/fees-and-costs.html) gives 0.5% brokerage with R110 minimum, 0.25% purchase-only STT, Strate 0.006018% bounded by R6.29/R142.20, and levy 0.00033%. Retrieved HTML hash: `b105e6b596d082f199d97f9b9f57089bd0ca0dfb9e3c42998511df31c891997c`. The specific statutory table is used; older contradictory futures footnotes are not blended into it.

The diagnostic assumes 15% VAT on brokerage, Strate and levy, with each component and its VAT rounded to cents, half up. Levy VAT and invoice rounding remain assumptions. At R10,000, buy fees are R158.76 and sell fees R133.76: R292.52 round trip at unchanged notional. Monthly account charges and data subscriptions are excluded and disclosed. This is a currently observed schedule, not verified September tariff applicability or the owner's account tier.

Sixteen combinations cover R1k/R10k/R50k/R100k with full spread/per-side slip pairs 0/0, 10/10, 25/10 and 50/25 bps. Flat-price spread/slippage drag is one full spread plus two slips. No performance, liquidity capacity, broker fills or replay fee compatibility is inferred. The generic replay fee model remains unchanged; a verified asymmetric fee adapter is still needed before real-account replay admission.

## Reproduce offline

Frozen files and `audit.json` live under `artifacts/research/local_b5_2026_10_05/`. From the repository root:

```powershell
& $taskPython scripts/audit_local_backtest_sources.py --daily artifacts/research/local_b5_2026_10_05/data/yahoo-SOL-daily.json --intraday artifacts/research/local_b5_2026_10_05/data/yahoo-SOL-30m.json --source-receipts artifacts/research/local_b5_2026_10_05/data/official-source-receipts.json --alpha-search artifacts/research/local_b5_2026_10_05/data/alpha-sasol-search.json --output work/b5-audit-reproduced.json
```

The dated CLI assesses this SOL pilot, while `domain.backtest.acceptance.compare_sources` is a generic pure diagnostic. Input file hashes and content fingerprints are recorded. Reproduction makes zero external requests and requires no credentials. Complete provider caches and secrets are excluded; the Alpha budget receipt retains only reservation times and safe result states.

Six additional independent tests cover fixed fee arithmetic, buy-only tax, bounded Strate, malformed/duplicated/reordered bars, missing metadata/identity, and refusal to self-certify admission even when aggregates match. Final safe-suite, mutation and protected results are recorded in the current milestone after completion.
