# Local historical SENS test — Sasol

5 October 2026. Isolated B5 extension, not dashboard integration or full engine acceptance.

Pilot identity: Sasol Limited, cash JSE SOL, ISIN ZAE000006896, Yahoo SOL.JO. Window: 1 September–2 October 2026 inclusive. Existing 23 daily and 368 30-minute Yahoo observations are unchanged.

| Source | Observed result | Coverage limit |
| --- | --- | --- |
| ShareData | Ten search results and ten parsed full-text notices, eleven bounded requests | Provider search, not certified complete exchange action history |
| Moneyweb | Ten exact-issuer search leads; four broader keyword matches excluded | Direct HTTP access blocked; public browser search works; subscriber text/PDF still gated after user sign-in report |
| Sharenet | One exact-issuer full-text notice from linked public 9 September archive, two bounded requests | Full window unverified; unlimited history/PDF subscription may be needed |

Twenty-one records group into ten releases. The 9 September 17:45 notice matches across all three sources; its first following observed 30-minute slot is 10 September 09:00. This is post-hoc alignment, not a verified exchange session or executable fill. Original board-change and correction notices remain separate. Body content is hashed, not redistributed; normalized records retain public headlines, source URLs, receipt clocks and explicit identity/access states. No credentials or browser profile data are stored.

All records were obtained in October, so zero qualify as available by the 2 October cutoff. A reconstructed historical strategy would require a separately approved availability contract and cannot silently replace the actual receipt clock. ShareData header 17:45 conflicts with ambiguous footer 05:45; Moneyweb machine +00:00 clocks conflict with the same display interpreted as SAST. Diagnostics preserve both instead of choosing a more convenient timestamp.

The adapter extends existing SENSFeedFetcher/normalization; optional event context cannot alter trades, scores or corporate-action adjustments. New source policies remain disabled. See ADR 0048. The CLI requires an explicit acquisition subcommand, limits requests to twelve and dates to at most 32 inclusive calendar dates, refuses redirects, caps responses and does not retry blocked access. Imported search snapshots are metadata only. Empty/unavailable searches do not certify an announcement-free interval.

## Operating interface

From repository root, using the existing virtual environment:

```powershell
python scripts/local_sens_history.py fetch-sharedata --start 2026-09-01 --end 2026-10-02 --instrument SOL.JO --issuer "SASOL LIMITED" --code SOL --isin ZAE000006896 --output work/sharedata.json
python scripts/local_sens_history.py import-search --source moneyweb_sens --snapshot work/public-search.html --url "https://www.moneyweb.co.za/tools-and-data/moneyweb-sens/?search=Sasol&startDate=2026-09-01&endDate=2026-10-02" --retrieved-at "2026-10-05T15:04:17.182+00:00" --instrument SOL.JO --issuer "SASOL LIMITED" --code SOL --isin ZAE000006896 --output work/moneyweb-leads.json
python scripts/local_sens_history.py audit --evidence artifacts/research/local_sens_2026_10_05/evidence.json --daily artifacts/research/local_b5_2026_10_05/data/yahoo-SOL-daily.json --intraday artifacts/research/local_b5_2026_10_05/data/yahoo-SOL-30m.json --as-of 2026-10-02T23:59:59+02:00 --output work/sens-audit.json
```

Sharenet search/body parsers use the same import/parse contracts and bounded fetcher. Its full-window automated archive collector is not established. Moneyweb subscriber automation is not established; a browser login does not authorize copying cookies to the HTTP client. Import only visible owner-permitted content with its genuine capture URL/time. Do not invent dates when importing.

## Price-data and integration questions

The signed-in [Sasol chart](https://www.sharedata.co.za/v2/Scripts/Chart.aspx?c=SOL&x=JSE) offers OHLC/candlestick displays and Daily/Weekly/Monthly periods. The quote page shows delayed intraday prices and recent trades. No free historical OHLCV CSV or historical 30-minute export was verified in the inspected controls. [Profile's separate downloader](https://www.profile.co.za/chart_downloads.htm) advertises end-of-day CSV and delayed intraday updates for charting packages, with corporate-action adjustments; an hourly snapshot is not proof of complete historical intraday bars. [ShareData FAQ](https://www.sharedata.co.za/v2/Scripts/Directory/FAQ/faq_General.aspx) distinguishes free, registered and subscribed access. Do not infer subscription/export entitlements just from being signed in.

Main dashboard integration can explicitly expose its existing read-only IG connection, permitting retests of missing links/history. It does not guarantee entitlements or depth, and IG CFD prices cannot silently fill cash-share OHLC gaps. Reverify instrument identity, interval/session coverage, units, account entitlement and product semantics when integration happens.

## Verification and remaining gates

917 safe offline tests passed in 87.294 seconds, including eleven new source/time/access/grouping tests. Protected artifacts: 54/54. Local CLI audit reproduces the frozen output. B5 still requires qualified sessions/actions, closing coverage and daily/intraday reconciliation, costs/capacity and executable FX/gold product evidence. The SENS pilot adds event provenance; it does not unblock those gates or establish profitability.
